from rest_framework import serializers

from apps.sports.serializers import OrganizationSerializer, SportSerializer

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    sport_slug = serializers.CharField(source="sport.slug", read_only=True)
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "organization",
            "organization_slug",
            "sport",
            "sport_slug",
            "title",
            "slug",
            "location",
            "country",
            "city",
            "start_date",
            "end_date",
            "source_url",
            "external_id",
            "status",
            "created_at",
            "updated_at",
        ]
