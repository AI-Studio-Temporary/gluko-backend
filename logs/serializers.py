from rest_framework import serializers

from .models import GlucoseLog, InsulinLog, MealLog


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
