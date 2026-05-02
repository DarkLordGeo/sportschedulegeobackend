from django_filters import rest_framework as filters

from .models import Event


class EventFilter(filters.FilterSet):
    sport = filters.CharFilter(field_name="sport__slug", lookup_expr="iexact")
    organization = filters.CharFilter(field_name="organization__slug", lookup_expr="iexact")
    country = filters.CharFilter(field_name="country", lookup_expr="iexact")
    start_date_after = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_before = filters.DateFilter(field_name="start_date", lookup_expr="lte")
    end_date_after = filters.DateFilter(field_name="end_date", lookup_expr="gte")
    end_date_before = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = [
            "sport",
            "organization",
            "country",
            "status",
            "start_date_after",
            "start_date_before",
            "end_date_after",
            "end_date_before",
        ]
