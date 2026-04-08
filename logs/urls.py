from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BolusCalculateView,
    BolusHistoryView,
    GlucoseLogViewSet,
    InsulinLogViewSet,
    MealLogViewSet,
    SportLogViewSet,
)

router = DefaultRouter()
router.register('glucose', GlucoseLogViewSet, basename='glucose-log')
router.register('insulin', InsulinLogViewSet, basename='insulin-log')
router.register('meals', MealLogViewSet, basename='meal-log')
router.register('sport', SportLogViewSet, basename='sport-log')

urlpatterns = router.urls + [
    path('bolus/calculate/', BolusCalculateView.as_view(), name='bolus-calculate'),
    path('bolus/history/', BolusHistoryView.as_view(), name='bolus-history'),
]
