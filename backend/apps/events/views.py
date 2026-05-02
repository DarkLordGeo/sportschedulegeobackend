from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .filters import EventFilter
from .models import Event
from .serializers import EventSerializer


class EventViewSet(ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    filterset_class = EventFilter

    def get_queryset(self) -> QuerySet[Event]:
        queryset = Event.objects.select_related("sport", "organization")
        today = timezone.localdate()

        if self.action == "archive":
            return queryset.filter(start_date__lt=today).order_by("-start_date", "title")

        if self.action == "list":
            georgia_related = (
                Q(country__iexact="Georgia")
                | Q(city__iexact="Tbilisi")
                | Q(title__icontains="Georgia")
                | Q(title__icontains="Tbilisi")
            )
            return (
                queryset.filter(start_date__gte=today)
                .annotate(
                    local_priority=Case(
                        When(georgia_related, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
                .order_by("local_priority", "start_date")
            )

        return queryset

    @action(detail=False, methods=["get"], url_path="archive")
    def archive(self, request, *args, **kwargs) -> Response:
        return self.list(request, *args, **kwargs)
