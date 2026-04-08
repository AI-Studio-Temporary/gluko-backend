from rest_framework.routers import DefaultRouter

from .views import GlucoseLogViewSet, InsulinLogViewSet, MealLogViewSet

router = DefaultRouter()
router.register('glucose', GlucoseLogViewSet, basename='glucose-log')
router.register('insulin', InsulinLogViewSet, basename='insulin-log')
router.register('meals', MealLogViewSet, basename='meal-log')

urlpatterns = router.urls
