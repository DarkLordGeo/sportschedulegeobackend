from django.db.models import QuerySet
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import EventFilter
from .models import Event
from .serializers import EventSerializer


class EventViewSet(ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    filterset_class = EventFilter

    def get_queryset(self) -> QuerySet[Event]:
        return Event.objects.select_related("sport", "organization")
