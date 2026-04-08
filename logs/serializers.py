from rest_framework import serializers

from .models import GlucoseLog, InsulinLog, MealLog, SportLog, BolusCalculation


class GlucoseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlucoseLog
        fields = ['id', 'value_mgdl', 'measurement_context', 'notes', 'logged_at']
        read_only_fields = ['id']


class InsulinLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsulinLog
        fields = ['id', 'units', 'insulin_type', 'insulin_brand', 'injection_site', 'notes', 'logged_at']
        read_only_fields = ['id']


class MealLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealLog
        fields = [
            'id', 'description', 'estimated_carbs', 'carb_source',
            'image_url', 'meal_type', 'notes', 'logged_at',
        ]
        read_only_fields = ['id']


class SportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportLog
        fields = [
            'id', 'activity_type', 'duration_min', 'intensity',
            'glucose_before', 'glucose_after', 'notes', 'logged_at',
        ]
        read_only_fields = ['id']


class BolusCalculateSerializer(serializers.Serializer):
    carbohydrates_g = serializers.DecimalField(max_digits=7, decimal_places=2)
    current_glucose = serializers.DecimalField(max_digits=5, decimal_places=2)
    meal_log_id = serializers.IntegerField(required=False)


class BolusCalculationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BolusCalculation
        fields = [
            'id', 'carbohydrates_g', 'current_glucose', 'target_glucose',
            'icr_used', 'isf_used', 'meal_dose', 'correction_dose',
            'total_dose', 'calculated_at',
        ]
        read_only_fields = fields
