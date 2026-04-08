"""Orchestrator — intent classification + agent routing.

This is the single entry point for all chat messages.
"""

import logging

from . import bolus, carb, log_agent, safety, summary, tutor
from .base import call_llm, parse_json_response
from .prompts import GREETING_RESPONSES, ORCHESTRATOR_SYSTEM, OUT_OF_SCOPE_RESPONSE

logger = logging.getLogger(__name__)


class AgentResult:
    """Structured result from agent processing."""

    def __init__(self, content: str, agent_used: str, intent: str, confidence: float = 1.0):
        self.content = content
        self.agent_used = agent_used
        self.intent = intent
        self.confidence = confidence


class Orchestrator:
    """Process a user message through safety gate, intent classification, and sub-agent routing."""

    def process(self, message: str, history: list[dict], user) -> AgentResult:
        # ── 1. Safety gate (always first) ─────────────────
        emergency = safety.check_safety(message)
        if emergency:
            return AgentResult(
                content=emergency['response'],
                agent_used='safety_gate',
                intent='emergency',
                confidence=1.0,
            )

        # ── 2. Get user profile context ───────────────────
        profile_context = ''
        try:
            profile_context = user.profile.to_context_string()
        except Exception:
            pass

        # ── 3. Classify intent ────────────────────────────
        intent_data = self._classify_intent(message, history)
        intent = intent_data.get('intent', 'diabetes_question')
        confidence = intent_data.get('confidence', 0.5)
        entities = intent_data.get('entities', {})

        logger.info('Intent: %s (%.2f) | Entities: %s', intent, confidence, entities)

        # ── 4. Route to sub-agent ─────────────────────────
        if intent == 'greeting':
            msg_lower = message.lower().strip()
            for key, response in GREETING_RESPONSES.items():
                if key in msg_lower:
                    return AgentResult(response, 'orchestrator', intent, confidence)
            return AgentResult(GREETING_RESPONSES.get('hi', 'Hey! How can I help?'), 'orchestrator', intent, confidence)

        if intent == 'out_of_scope':
            return AgentResult(OUT_OF_SCOPE_RESPONSE, 'orchestrator', intent, confidence)

        if intent == 'diabetes_question':
            content = tutor.handle(message, history, profile_context)
            return AgentResult(content, 'tutor', intent, confidence)

        if intent == 'food_log':
            content = carb.handle(message, history, user, entities)
            return AgentResult(content, 'carb_estimator', intent, confidence)

        if intent == 'glucose_log':
            content = log_agent.handle_glucose(message, user, entities)
            return AgentResult(content, 'log_agent', intent, confidence)

        if intent == 'insulin_log':
            content = log_agent.handle_insulin(message, user, entities)
            return AgentResult(content, 'log_agent', intent, confidence)

        if intent == 'activity_log':
            content = log_agent.handle_activity(message, user, entities)
            return AgentResult(content, 'log_agent', intent, confidence)

        if intent == 'bolus_request':
            content = bolus.handle(message, user, entities)
            return AgentResult(content, 'bolus_calculator', intent, confidence)

        if intent == 'summary_request':
            content = summary.handle(user)
            return AgentResult(content, 'summary', intent, confidence)

        if intent == 'profile_query':
            content = tutor.handle(message, history, profile_context)
            return AgentResult(content, 'tutor', intent, confidence)

        # Fallback: treat as diabetes question
        content = tutor.handle(message, history, profile_context)
        return AgentResult(content, 'tutor', intent, confidence)

    def _classify_intent(self, message: str, history: list[dict]) -> dict:
        """Use LLM to classify user intent."""
        # Build context from recent history
        recent = history[-6:] if len(history) > 6 else history
        context_msgs = recent + [{'role': 'user', 'content': message}]

        try:
            raw = call_llm(
                ORCHESTRATOR_SYSTEM,
                context_msgs,
                json_mode=True,
                temperature=0.1,
                max_tokens=256,
            )
            return parse_json_response(raw)
        except Exception as e:
            logger.error('Intent classification failed: %s', e)
            return {'intent': 'diabetes_question', 'confidence': 0.3, 'entities': {}}
