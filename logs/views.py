from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import GlucoseLog, InsulinLog, MealLog
from .serializers import GlucoseLogSerializer, InsulinLogSerializer, MealLogSerializer


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
