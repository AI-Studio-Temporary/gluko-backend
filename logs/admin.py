from django.contrib import admin

from .models import GlucoseLog, InsulinLog, MealLog, SportLog, BolusCalculation


@admin.register(GlucoseLog)
class GlucoseLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'value_mgdl', 'measurement_context', 'logged_at')
    list_filter = ('measurement_context', 'logged_at')


@admin.register(InsulinLog)
class InsulinLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'units', 'insulin_type', 'logged_at')
    list_filter = ('insulin_type', 'logged_at')


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'description_short', 'estimated_carbs', 'meal_type', 'logged_at')
    list_filter = ('meal_type', 'carb_source', 'logged_at')

    @admin.display(description='Description')
    def description_short(self, obj):
        return obj.description[:80]


@admin.register(SportLog)
class SportLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_type', 'duration_min', 'intensity', 'logged_at')
    list_filter = ('intensity', 'logged_at')


@admin.register(BolusCalculation)
class BolusCalculationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'carbohydrates_g', 'total_dose', 'calculated_at')
    list_filter = ('calculated_at',)
