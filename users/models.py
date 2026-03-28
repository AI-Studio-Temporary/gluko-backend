from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT = 'prefer_not_to_say', 'Prefer not to say'

    class DiabetesType(models.TextChoices):
        TYPE1 = 'type1', 'Type 1'
        TYPE2 = 'type2', 'Type 2'
        GESTATIONAL = 'gestational', 'Gestational'
        LADA = 'lada', 'LADA (Type 1.5)'
        MODY = 'mody', 'MODY'
        PREDIABETES = 'prediabetes', 'Prediabetes'
        OTHER = 'other', 'Other'

    class InsulinRegimen(models.TextChoices):
        MDI = 'mdi', 'Multiple Daily Injections (MDI)'
        PUMP = 'pump', 'Insulin Pump (CSII)'
        BASAL_ONLY = 'basal_only', 'Basal Only'
        PREMIXED = 'premixed', 'Premixed Insulin'
        NONE = 'none', 'Not on Insulin'

    class MonitoringMethod(models.TextChoices):
        CGM = 'cgm', 'Continuous Glucose Monitor (CGM)'
        FINGER_PRICK = 'finger_prick', 'Finger Prick'
        BOTH = 'both', 'Both CGM & Finger Prick'
        NONE = 'none', 'None currently'

    class ActivityLevel(models.TextChoices):
        SEDENTARY = 'sedentary', 'Sedentary (little or no exercise)'
        LIGHT = 'light', 'Light (1–3 days/week)'
        MODERATE = 'moderate', 'Moderate (3–5 days/week)'
        ACTIVE = 'active', 'Active (6–7 days/week)'
        VERY_ACTIVE = 'very_active', 'Very Active (twice/day or physical job)'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # ── Personal ──────────────────────────────────────────
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    # ── Diabetes diagnosis ────────────────────────────────
    diabetes_type = models.CharField(max_length=20, choices=DiabetesType.choices, blank=True)
    diagnosis_year = models.PositiveIntegerField(null=True, blank=True)

    # ── Insulin ───────────────────────────────────────────
    on_insulin = models.BooleanField(default=False)
    insulin_regimen = models.CharField(max_length=20, choices=InsulinRegimen.choices, blank=True)
    insulin_type = models.CharField(max_length=200, blank=True, help_text='e.g. Novorapid + Lantus')
    insulin_to_carb_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Grams of carbs covered by 1 unit of insulin'
    )
    insulin_sensitivity_factor = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        help_text='mmol/L drop per 1 unit of correction insulin'
    )

    # ── Targets & recent labs ─────────────────────────────
    target_bg_min = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text='mmol/L')
    target_bg_max = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text='mmol/L')
    last_hba1c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text='%')

    # ── Monitoring ────────────────────────────────────────
    monitoring_method = models.CharField(max_length=20, choices=MonitoringMethod.choices, blank=True)
    cgm_device = models.CharField(max_length=100, blank=True, help_text='e.g. Dexcom G7, Libre 3')

    # ── Other health context ──────────────────────────────
    other_medications = models.TextField(blank=True, help_text='List any other medications you take')
    other_conditions = models.TextField(blank=True, help_text='e.g. hypertension, coeliac disease')
    dietary_restrictions = models.TextField(blank=True, help_text='e.g. vegetarian, gluten-free, low-carb')
    activity_level = models.CharField(max_length=20, choices=ActivityLevel.choices, blank=True)
    management_goals = models.TextField(blank=True, help_text='What are your main diabetes management goals?')

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile({self.user.email})'

    def to_context_string(self) -> str:
        """Return a natural-language summary for injecting into the AI system prompt."""
        parts = []

        if self.first_name:
            parts.append(f"The user's name is {self.first_name}.")

        if self.diabetes_type:
            label = self.DiabetesType(self.diabetes_type).label
            parts.append(f"They have {label} diabetes.")
            if self.diagnosis_year:
                parts.append(f"Diagnosed in {self.diagnosis_year}.")

        if self.on_insulin:
            regimen = self.InsulinRegimen(self.insulin_regimen).label if self.insulin_regimen else ''
            insulin = self.insulin_type or ''
            if regimen or insulin:
                parts.append(f"Insulin therapy: {regimen}{' — ' + insulin if insulin else ''}.")
            if self.insulin_to_carb_ratio:
                parts.append(f"Insulin-to-carb ratio: 1 unit per {self.insulin_to_carb_ratio} g carbs.")
            if self.insulin_sensitivity_factor:
                parts.append(f"Insulin sensitivity factor: 1 unit drops BG by {self.insulin_sensitivity_factor} mmol/L.")
        else:
            parts.append("Not currently on insulin.")

        if self.target_bg_min and self.target_bg_max:
            parts.append(f"Target blood glucose range: {self.target_bg_min}–{self.target_bg_max} mmol/L.")
        if self.last_hba1c:
            parts.append(f"Most recent HbA1c: {self.last_hba1c}%.")

        if self.monitoring_method:
            label = self.MonitoringMethod(self.monitoring_method).label
            parts.append(f"Glucose monitoring: {label}{' (' + self.cgm_device + ')' if self.cgm_device else ''}.")

        if self.weight_kg and self.height_cm:
            parts.append(f"Weight: {self.weight_kg} kg, Height: {self.height_cm} cm.")
        elif self.weight_kg:
            parts.append(f"Weight: {self.weight_kg} kg.")

        if self.activity_level:
            label = self.ActivityLevel(self.activity_level).label
            parts.append(f"Activity level: {label}.")

        if self.dietary_restrictions:
            parts.append(f"Dietary restrictions: {self.dietary_restrictions}.")

        if self.other_conditions:
            parts.append(f"Other health conditions: {self.other_conditions}.")

        if self.other_medications:
            parts.append(f"Other medications: {self.other_medications}.")

        if self.management_goals:
            parts.append(f"Their goals: {self.management_goals}.")

        return ' '.join(parts)
