from django_filters import rest_framework as filters
from django.db.models import Q

from .models import Event


class EventFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    sport = filters.CharFilter(field_name="sport__slug", lookup_expr="iexact")
    organization = filters.CharFilter(field_name="organization__slug", lookup_expr="iexact")
    country = filters.CharFilter(field_name="country", lookup_expr="iexact")
    city = filters.CharFilter(field_name="city", lookup_expr="iexact")
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    date_from = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="start_date", lookup_expr="lte")
    start_date_after = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_before = filters.DateFilter(field_name="start_date", lookup_expr="lte")
    end_date_after = filters.DateFilter(field_name="end_date", lookup_expr="gte")
    end_date_before = filters.DateFilter(field_name="end_date", lookup_expr="lte")

    def filter_search(self, queryset, _name, value):
        query = value.strip()
        if not query:
            return queryset
        return queryset.filter(
            Q(title__icontains=query)
            | Q(city__icontains=query)
            | Q(country__icontains=query)
            | Q(organization__name__icontains=query)
        )

    class Meta:
        model = Event
        fields = [
            "search",
            "sport",
            "organization",
            "country",
            "city",
            "status",
            "date_from",
            "date_to",
            "start_date_after",
            "start_date_before",
            "end_date_after",
            "end_date_before",
        ]
