"""Tutor agent — personalised diabetes Q&A."""

from .base import call_llm
from .prompts import TUTOR_SYSTEM


def handle(message: str, history: list[dict], profile_context: str) -> str:
    """Answer a diabetes-related question with personalisation."""
    system = TUTOR_SYSTEM.format(profile_context=profile_context or 'No profile data available.')
    return call_llm(system, history, temperature=0.7, max_tokens=1024)
