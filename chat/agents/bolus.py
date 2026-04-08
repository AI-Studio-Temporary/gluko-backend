"""Bolus agent — rule-based insulin dose calculation (no LLM call)."""

from decimal import Decimal, ROUND_HALF_UP

from logs.models import BolusCalculation

DISCLAIMER = (
    "This is a mathematical calculation based on YOUR settings, not a medical "
    "prescription. Always use your clinical judgement and consult your healthcare "
    "provider. Factors like active insulin, exercise, and illness can affect your "
    "actual needs."
)


def _round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def handle(message: str, user, entities: dict) -> str:
    """Calculate bolus dose from profile settings."""
    profile = getattr(user, 'profile', None)
    if not profile or not profile.insulin_to_carb_ratio or not profile.insulin_sensitivity_factor:
        return (
            "I need your insulin-to-carb ratio (ICR) and insulin sensitivity factor (ISF) "
            "to calculate a bolus dose. Please set these in your **Profile** first."
        )

    icr = profile.insulin_to_carb_ratio
    isf = profile.insulin_sensitivity_factor
    target = profile.target_bg_min or Decimal('5.5')

    carbs = entities.get('carbs_g')
    glucose = entities.get('current_glucose')

    if carbs is None:
        return "How many grams of carbs are you eating? (e.g. \"60g carbs, glucose is 8.5\")"
    if glucose is None:
        return f"What's your current blood glucose? I'll calculate the dose for {carbs}g carbs."

    carbs = Decimal(str(carbs))
    glucose = Decimal(str(glucose))

    meal_dose = _round2(carbs / icr)
    correction = _round2((glucose - target) / isf) if glucose > target else Decimal('0.00')
    total = _round2(meal_dose + correction)

    # Save to DB
    BolusCalculation.objects.create(
        user=user,
        carbohydrates_g=carbs,
        current_glucose=glucose,
        target_glucose=target,
        icr_used=icr,
        isf_used=isf,
        meal_dose=meal_dose,
        correction_dose=correction,
        total_dose=total,
    )

    correction_text = (
        f"Correction: ({glucose} - {target}) / {isf} (ISF) = **{correction} units**"
        if glucose > target
        else "Correction: not needed (glucose at or below target)"
    )

    return (
        f"**Bolus Calculation**\n\n"
        f"Meal dose: {carbs}g / {icr} (ICR) = **{meal_dose} units**\n"
        f"{correction_text}\n\n"
        f"**Total suggested dose: {total} units**\n\n"
        f"_{DISCLAIMER}_"
    )
