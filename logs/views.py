from decimal import Decimal, ROUND_HALF_UP

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import BolusCalculation, GlucoseLog, InsulinLog, MealLog, SportLog
from .serializers import (
    BolusCalculateSerializer,
    BolusCalculationSerializer,
    GlucoseLogSerializer,
    InsulinLogSerializer,
    MealLogSerializer,
    SportLogSerializer,
)

BOLUS_DISCLAIMER = (
    "This is a mathematical calculation based on YOUR settings, not a medical "
    "prescription. Always use your clinical judgement and consult your healthcare "
    "provider. Factors like active insulin, exercise, and illness can affect your "
    "actual needs."
)


class BaseLogViewSet(ModelViewSet):
    """Base viewset for all health log types. List + Create + Destroy only."""

    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = self.model_class.objects.filter(user=self.request.user)
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(logged_at__date=date)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GlucoseLogViewSet(BaseLogViewSet):
    model_class = GlucoseLog
    serializer_class = GlucoseLogSerializer


class InsulinLogViewSet(BaseLogViewSet):
    model_class = InsulinLog
    serializer_class = InsulinLogSerializer


class MealLogViewSet(BaseLogViewSet):
    model_class = MealLog
    serializer_class = MealLogSerializer


class SportLogViewSet(BaseLogViewSet):
    model_class = SportLog
    serializer_class = SportLogSerializer


# ── Bolus Calculator ─────────────────────────────────────────


def _round2(value):
    """Round a Decimal to 2 decimal places."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class BolusCalculateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BolusCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = getattr(request.user, 'profile', None)
        if not profile or not profile.insulin_to_carb_ratio or not profile.insulin_sensitivity_factor:
            return Response(
                {'detail': 'Please set your insulin-to-carb ratio (ICR) and insulin sensitivity factor (ISF) in your profile.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        icr = profile.insulin_to_carb_ratio
        isf = profile.insulin_sensitivity_factor
        target = profile.target_bg_min or Decimal('5.5')

        carbs = serializer.validated_data['carbohydrates_g']
        current = serializer.validated_data['current_glucose']

        meal_dose = _round2(carbs / icr)
        correction_dose = _round2((current - target) / isf) if current > target else Decimal('0.00')
        total_dose = _round2(meal_dose + correction_dose)

        # Resolve optional meal_log
        meal_log = None
        meal_log_id = serializer.validated_data.get('meal_log_id')
        if meal_log_id:
            meal_log = MealLog.objects.filter(id=meal_log_id, user=request.user).first()

        calc = BolusCalculation.objects.create(
            user=request.user,
            meal_log=meal_log,
            carbohydrates_g=carbs,
            current_glucose=current,
            target_glucose=target,
            icr_used=icr,
            isf_used=isf,
            meal_dose=meal_dose,
            correction_dose=correction_dose,
            total_dose=total_dose,
        )

        return Response({
            'id': calc.id,
            'meal_dose': float(meal_dose),
            'correction_dose': float(correction_dose),
            'total_dose': float(total_dose),
            'formula': {
                'meal': f'{carbs}g / {icr} (ICR) = {meal_dose} units',
                'correction': f'({current} - {target}) / {isf} (ISF) = {correction_dose} units'
                if current > target else 'No correction needed (glucose at or below target)',
            },
            'disclaimer': BOLUS_DISCLAIMER,
        }, status=status.HTTP_201_CREATED)


class BolusHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        calcs = BolusCalculation.objects.filter(user=request.user)
        serializer = BolusCalculationSerializer(calcs, many=True)
        return Response(serializer.data)
