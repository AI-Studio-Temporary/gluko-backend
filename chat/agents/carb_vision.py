"""Carb estimation from a food image — uses OpenAI vision (gpt-4o-mini)."""

import base64
import logging

from logs.models import MealLog

from .base import get_openai_client, parse_json_response
from .prompts import CARB_ESTIMATION_SYSTEM

logger = logging.getLogger(__name__)


def handle(image_bytes: bytes, mime_type: str, hint: str, user) -> str:
    """Estimate carbs from an image and save to MealLog."""
    client = get_openai_client()
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f'data:{mime_type};base64,{b64}'

    user_text = (
        f'Estimate the carbs in this meal photo. User hint: {hint!r}'
        if hint
        else 'Estimate the carbs in this meal photo.'
    )

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=600,
        messages=[
            {'role': 'system', 'content': CARB_ESTIMATION_SYSTEM},
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': user_text},
                    {'type': 'image_url', 'image_url': {'url': data_url}},
                ],
            },
        ],
    )
    raw = response.choices[0].message.content
    data = parse_json_response(raw)

    if not data or 'total_carbs_g' not in data:
        return "I couldn't read carbs from that photo. Try another angle or describe the meal in text."

    total = data['total_carbs_g']
    description = data.get('meal_description') or hint or 'Meal from photo'

    MealLog.objects.create(
        user=user,
        description=description,
        estimated_carbs=total,
        carb_source='ai_image',
        meal_type=_guess_meal_type(),
    )

    items_text = '\n'.join(
        f"  - {i['name']}: **{i['carbs_g']}g** ({i.get('confidence', 'medium')})"
        for i in data.get('items', [])
    )
    reply = (
        f'**Meal logged from photo** — {description}\n\n'
        f'{items_text}\n\n'
        f'**Total: {total}g carbs** (confidence: {data.get("confidence", "medium")})\n'
    )
    if data.get('notes'):
        reply += f'\n_{data["notes"]}_\n'
    reply += '\nSaved to your meal log.'
    return reply


def _guess_meal_type() -> str:
    """Guess meal type based on time of day."""
    from django.utils import timezone
    hour = timezone.localtime().hour
    if hour < 10:
        return 'breakfast'
    if hour < 14:
        return 'lunch'
    if hour < 17:
        return 'snack'
    return 'dinner'
