from rest_framework import serializers

from .models import Organization, Sport


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ["id", "name", "slug"]


class OrganizationSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    sport_slug = serializers.CharField(source="sport.slug", read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "website_url", "sport", "sport_slug"]
