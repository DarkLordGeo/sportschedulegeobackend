from __future__ import annotations

from django.db import models


class ScrapeRunStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    PARTIAL = "partial", "Partial"


class ScrapeRun(models.Model):
    source_name = models.CharField(max_length=150)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ScrapeRunStatus.choices,
        default=ScrapeRunStatus.RUNNING,
    )
    total_found = models.PositiveIntegerField(default=0)
    total_created = models.PositiveIntegerField(default=0)
    total_updated = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["source_name", "status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_name} - {self.status} at {self.started_at:%Y-%m-%d %H:%M:%S}"
