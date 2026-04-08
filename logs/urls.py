from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BolusCalculateView,
    BolusHistoryView,
    DashboardSummaryView,
    GlucoseLogViewSet,
    InsulinLogViewSet,
    MealLogViewSet,
    SportLogViewSet,
    TrendsView,
)

router = DefaultRouter()
router.register('glucose', GlucoseLogViewSet, basename='glucose-log')
router.register('insulin', InsulinLogViewSet, basename='insulin-log')
router.register('meals', MealLogViewSet, basename='meal-log')
router.register('sport', SportLogViewSet, basename='sport-log')

urlpatterns = router.urls + [
    path('bolus/calculate/', BolusCalculateView.as_view(), name='bolus-calculate'),
    path('bolus/history/', BolusHistoryView.as_view(), name='bolus-history'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/trends/', TrendsView.as_view(), name='dashboard-trends'),
]
