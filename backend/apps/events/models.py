from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.sports.models import Organization, Sport


class EventStatus(models.TextChoices):
    UPCOMING = "upcoming", "Upcoming"
    LIVE = "live", "Live"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    UNKNOWN = "unknown", "Unknown"


class Event(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="events",
    )
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280)
    location = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    source_url = models.URLField(unique=True)
    external_id = models.CharField(max_length=150, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.UNKNOWN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "external_id"],
                name="unique_event_external_id_per_organization",
                condition=~Q(external_id=""),
            ),
            models.UniqueConstraint(
                fields=["organization", "slug", "start_date"],
                name="unique_event_slug_date_per_organization",
            ),
        ]
        indexes = [
            models.Index(fields=["sport", "status"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["country"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.start_date})"
