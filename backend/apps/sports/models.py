from __future__ import annotations

from django.db import models


class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    website_url = models.URLField(blank=True)
    sport = models.ForeignKey(
        Sport,
        on_delete=models.CASCADE,
        related_name="organizations",
    )

    class Meta:
        ordering = ["sport__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["sport", "slug"],
                name="unique_organization_slug_per_sport",
            )
        ]
        indexes = [
            models.Index(fields=["sport", "slug"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.sport.name})"
