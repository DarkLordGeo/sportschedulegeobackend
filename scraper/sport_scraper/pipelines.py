from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import django
import environ
from django.conf import settings
from django.utils import timezone
from scrapy.exceptions import DropItem


def setup_django() -> None:
    project_root = Path(__file__).resolve().parents[2]
    environ.Env.read_env(project_root / ".env", overwrite=False)
    environ.Env.read_env(project_root / "scraper" / ".env", overwrite=False)

    backend_path = project_root / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


setup_django()

from apps.events.models import Event, EventStatus  # noqa: E402
from apps.scraping_logs.models import ScrapeRun, ScrapeRunStatus  # noqa: E402
from apps.sports.models import Organization, Sport  # noqa: E402


class DjangoEventPipeline:
    """Persist normalized scraper items through Django ORM into the shared database."""

    def open_spider(self, spider: Any) -> None:
        if not settings.DEBUG and not os.environ.get("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL is required when running the scraper in production.")

        self.run = ScrapeRun.objects.create(
            source_name=getattr(spider, "source_name", spider.name),
            started_at=timezone.now(),
            status=ScrapeRunStatus.RUNNING,
        )
        self.total_found = 0
        self.total_created = 0
        self.total_updated = 0
        self.total_skipped = 0

    def process_item(self, item: dict[str, Any], spider: Any) -> dict[str, Any]:
        self.total_found += 1
        required_fields = ["title", "start_date", "source_url", "sport_slug", "organization_slug"]
        missing_fields = [field for field in required_fields if not item.get(field)]
        if missing_fields:
            self.total_skipped += 1
            spider.logger.warning(
                "Skipping invalid event missing %s: %s",
                ", ".join(missing_fields),
                dict(item),
            )
            raise DropItem(f"Missing required event fields: {', '.join(missing_fields)}")

        sport, _ = Sport.objects.get_or_create(
            slug=item["sport_slug"],
            defaults={"name": item.get("sport_name") or item["sport_slug"].title()},
        )
        organization, _ = Organization.objects.get_or_create(
            sport=sport,
            slug=item["organization_slug"],
            defaults={
                "name": item.get("organization_name") or item["organization_slug"].upper(),
                "website_url": item.get("organization_website_url", ""),
            },
        )

        lookup: dict[str, Any]
        external_id = item.get("external_id") or ""
        if external_id:
            lookup = {"organization": organization, "external_id": external_id}
        else:
            lookup = {"source_url": item["source_url"]}

        defaults = {
            "organization": organization,
            "sport": sport,
            "title": item["title"],
            "slug": item["slug"],
            "location": item.get("location", ""),
            "country": item.get("country", ""),
            "city": item.get("city", ""),
            "start_date": item["start_date"],
            "end_date": item.get("end_date"),
            "source_url": item["source_url"],
            "external_id": external_id,
            "status": item.get("status") or EventStatus.UNKNOWN,
        }
        _, created = Event.objects.update_or_create(defaults=defaults, **lookup)
        if created:
            self.total_created += 1
        else:
            self.total_updated += 1
        return item

    def close_spider(self, spider: Any) -> None:
        error_message = ""
        status = ScrapeRunStatus.SUCCESS
        if getattr(spider, "crawler", None):
            stats = spider.crawler.stats.get_stats()
            error_count = stats.get("log_count/ERROR", 0)
            finish_reason = stats.get("finish_reason")
            if error_count:
                status = ScrapeRunStatus.PARTIAL
                error_message = f"Scrapy logged {error_count} error(s). Check scraper logs."
            if finish_reason not in {None, "finished"}:
                status = ScrapeRunStatus.FAILED
                error_message = f"Spider finished with reason: {finish_reason}."
            if self.total_skipped:
                skipped_message = f"Skipped {self.total_skipped} invalid event(s)."
                error_message = f"{error_message} {skipped_message}".strip()
                if status == ScrapeRunStatus.SUCCESS:
                    status = ScrapeRunStatus.PARTIAL

        self.run.finished_at = timezone.now()
        self.run.status = status
        self.run.total_found = self.total_found
        self.run.total_created = self.total_created
        self.run.total_updated = self.total_updated
        self.run.error_message = error_message
        self.run.save()
