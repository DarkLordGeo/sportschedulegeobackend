from django.db.models import QuerySet
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Organization, Sport
from .serializers import OrganizationSerializer, SportSerializer


class SportViewSet(ReadOnlyModelViewSet):
    queryset = Sport.objects.all()
    serializer_class = SportSerializer
    lookup_field = "slug"


class OrganizationViewSet(ReadOnlyModelViewSet):
    serializer_class = OrganizationSerializer
    lookup_field = "slug"
    filterset_fields = {
        "sport__slug": ["exact"],
        "sport__id": ["exact"],
    }

    def get_queryset(self) -> QuerySet[Organization]:
        return Organization.objects.select_related("sport")
