"""Log agent — extract structured health data from natural language and persist."""

import logging

from django.utils import timezone

from logs.models import GlucoseLog, InsulinLog, SportLog

logger = logging.getLogger(__name__)


def handle_glucose(message: str, user, entities: dict) -> str:
    """Log a glucose reading extracted from the user's message."""
    value = entities.get('value')
    if value is None:
        return "I couldn't find a glucose value in your message. Could you tell me your reading? (e.g. \"My glucose is 120 mg/dL\")"

    value = int(float(value))
    unit = entities.get('unit', 'mg/dL')
    context = entities.get('context', 'other')

    # Convert mmol/L to mg/dL if needed
    if unit == 'mmol/L' or value < 35:  # likely mmol/L
        value = round(value * 18)

    valid_contexts = ['fasting', 'before_meal', 'after_meal', 'bedtime', 'other']
    if context not in valid_contexts:
        context = 'other'

    GlucoseLog.objects.create(
        user=user,
        value_mgdl=value,
        measurement_context=context,
        logged_at=timezone.now(),
    )

    # Contextual feedback
    feedback = ''
    if value < 70:
        feedback = '\n\n**Note:** This is below the typical target range (70-180 mg/dL). Consider having a snack.'
    elif value > 180:
        feedback = '\n\n**Note:** This is above the typical target range (70-180 mg/dL).'

    return f"**Glucose logged:** {value} mg/dL ({context.replace('_', ' ')}){feedback}"


def handle_insulin(message: str, user, entities: dict) -> str:
    """Log an insulin dose extracted from the user's message."""
    units = entities.get('units')
    if units is None:
        return "How many units did you take? (e.g. \"4.5 units of Novorapid\")"

    units = float(units)
    insulin_type = entities.get('type', 'bolus')
    brand = entities.get('brand', '')

    valid_types = ['bolus', 'basal', 'correction']
    if insulin_type not in valid_types:
        insulin_type = 'bolus'

    InsulinLog.objects.create(
        user=user,
        units=units,
        insulin_type=insulin_type,
        insulin_brand=brand,
        logged_at=timezone.now(),
    )

    brand_text = f' ({brand})' if brand else ''
    return f"**Insulin logged:** {units} units {insulin_type}{brand_text}"


def handle_activity(message: str, user, entities: dict) -> str:
    """Log a sport activity extracted from the user's message."""
    activity = entities.get('activity')
    duration = entities.get('duration_min')

    if not activity:
        return "What activity did you do? (e.g. \"30 minute run\")"
    if not duration:
        return f"How long did you {activity}? (e.g. \"30 minutes\")"

    duration = int(float(duration))
    intensity = entities.get('intensity', 'moderate')
    valid_intensities = ['low', 'moderate', 'high']
    if intensity not in valid_intensities:
        intensity = 'moderate'

    SportLog.objects.create(
        user=user,
        activity_type=activity,
        duration_min=duration,
        intensity=intensity,
        logged_at=timezone.now(),
    )

    return f"**Activity logged:** {activity} — {duration} min ({intensity} intensity)"
