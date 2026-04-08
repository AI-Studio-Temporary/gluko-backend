"""Base utilities shared across all agents."""

import json
import logging

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def call_llm(
    system_prompt: str,
    messages: list[dict],
    model: str = 'gpt-4o-mini',
    max_tokens: int = 1024,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> str:
    """Call OpenAI chat completion and return the assistant's text."""
    client = get_openai_client()

    all_messages = [{'role': 'system', 'content': system_prompt}] + messages

    kwargs = {
        'model': model,
        'messages': all_messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }
    if json_mode:
        kwargs['response_format'] = {'type': 'json_object'}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def parse_json_response(text: str) -> dict:
    """Try to parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning('Failed to parse JSON from LLM: %s', text[:200])
        return {}
