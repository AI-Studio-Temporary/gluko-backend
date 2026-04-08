"""Carb estimation agent — text-based food to carbs."""

import json
import logging

from logs.models import MealLog

from .base import call_llm, parse_json_response
from .prompts import CARB_ESTIMATION_SYSTEM

logger = logging.getLogger(__name__)


def handle(message: str, history: list[dict], user, entities: dict) -> str:
    """Estimate carbs from a food description and save to MealLog."""
    food_desc = entities.get('food_description', message)

    result = call_llm(
        CARB_ESTIMATION_SYSTEM,
        [{'role': 'user', 'content': f'Estimate carbs for: {food_desc}'}],
        json_mode=True,
        temperature=0.3,
    )

    data = parse_json_response(result)
    if not data or 'total_carbs_g' not in data:
        return f"I estimated the carbs for your meal but had trouble structuring the result. Here's what I got:\n\n{result}"

    # Save to MealLog
    total_carbs = data['total_carbs_g']
    meal = MealLog.objects.create(
        user=user,
        description=food_desc,
        estimated_carbs=total_carbs,
        carb_source='ai_text',
        meal_type=_guess_meal_type(),
    )

    # Build response
    items_text = '\n'.join(
        f"  - {item['name']}: **{item['carbs_g']}g** ({item.get('confidence', 'medium')})"
        for item in data.get('items', [])
    )

    response = (
        f"**Meal logged** — {food_desc}\n\n"
        f"{items_text}\n\n"
        f"**Total: {total_carbs}g carbs** (confidence: {data.get('confidence', 'medium')})\n"
    )
    if data.get('notes'):
        response += f"\n_{data['notes']}_\n"

    response += "\nSaved to your meal log."
    return response


def _guess_meal_type() -> str:
    """Guess meal type based on time of day."""
    from django.utils import timezone
    hour = timezone.localtime().hour
    if hour < 10:
        return 'breakfast'
    elif hour < 14:
        return 'lunch'
    elif hour < 17:
        return 'snack'
    return 'dinner'
