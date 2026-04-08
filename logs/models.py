from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class GlucoseLog(models.Model):
    class MeasurementContext(models.TextChoices):
        FASTING = 'fasting', 'Fasting'
        BEFORE_MEAL = 'before_meal', 'Before meal'
        AFTER_MEAL = 'after_meal', 'After meal'
        BEDTIME = 'bedtime', 'Bedtime'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='glucose_logs')
    value_mgdl = models.PositiveIntegerField()
    measurement_context = models.CharField(
        max_length=20, choices=MeasurementContext.choices, default=MeasurementContext.OTHER,
    )
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f'{self.value_mgdl} mg/dL ({self.get_measurement_context_display()}) @ {self.logged_at}'


class InsulinLog(models.Model):
    class InsulinType(models.TextChoices):
        BOLUS = 'bolus', 'Bolus'
        BASAL = 'basal', 'Basal'
        CORRECTION = 'correction', 'Correction'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insulin_logs')
    units = models.DecimalField(max_digits=5, decimal_places=2)
    insulin_type = models.CharField(max_length=20, choices=InsulinType.choices)
    insulin_brand = models.CharField(max_length=100, blank=True)
    injection_site = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f'{self.units}u {self.get_insulin_type_display()} @ {self.logged_at}'


class MealLog(models.Model):
    class CarbSource(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        AI_TEXT = 'ai_text', 'AI (text)'
        AI_IMAGE = 'ai_image', 'AI (image)'
        AI_AUDIO = 'ai_audio', 'AI (audio)'

    class MealType(models.TextChoices):
        BREAKFAST = 'breakfast', 'Breakfast'
        LUNCH = 'lunch', 'Lunch'
        DINNER = 'dinner', 'Dinner'
        SNACK = 'snack', 'Snack'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_logs')
    description = models.TextField()
    estimated_carbs = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    carb_source = models.CharField(
        max_length=20, choices=CarbSource.choices, default=CarbSource.MANUAL,
    )
    image_url = models.URLField(blank=True)
    meal_type = models.CharField(
        max_length=20, choices=MealType.choices, default=MealType.SNACK,
    )
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        carbs = f'{self.estimated_carbs}g' if self.estimated_carbs else '?g'
        return f'{self.description[:40]} ({carbs}) @ {self.logged_at}'
