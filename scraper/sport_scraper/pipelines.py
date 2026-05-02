from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import django
from asgiref.sync import sync_to_async
from django.utils import timezone
from scrapy.exceptions import DropItem


def setup_django() -> None:
    project_root = Path(__file__).resolve().parents[2]
    backend_path = project_root / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


setup_django()

from apps.events.models import Event, EventStatus  # noqa: E402
from apps.scraping_logs.models import ScrapeRun, ScrapeRunStatus  # noqa: E402
from apps.sports.models import Organization, Sport  # noqa: E402


def slugify(value: str) -> str:
    """Simple slugify: lowercase, replace spaces/special chars with hyphens."""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value


class DjangoEventPipeline:
    """Persist normalized scraper items through Django ORM into the shared database."""

    @classmethod
    def from_crawler(cls, crawler: Any) -> "DjangoEventPipeline":
        instance = cls()
        instance.crawler = crawler
        return instance

    async def open_spider(self) -> None:
        self.total_found = 0
        self.total_created = 0
        self.total_updated = 0
        self.run = await sync_to_async(self._create_scrape_run)()

    async def process_item(self, item: dict[str, Any], spider: Any) -> dict[str, Any]:
        self.total_found += 1

        required_fields = ["title", "start_date", "source_url", "sport_slug", "organization_slug"]
        missing_fields = [field for field in required_fields if not item.get(field)]

        if missing_fields:
            raise DropItem(f"Missing required event fields: {', '.join(missing_fields)}")

        # Auto-generate slug from title if not provided
        if not item.get("slug"):
            item["slug"] = slugify(str(item["title"]))

        created = await sync_to_async(self._save_event)(item)

        if created:
            self.total_created += 1
        else:
            self.total_updated += 1

        return item

    async def close_spider(self) -> None:
        await sync_to_async(self._finish_scrape_run)()

    def _create_scrape_run(self) -> ScrapeRun:
        spider = self.crawler.spider
        return ScrapeRun.objects.create(
            source_name=getattr(spider, "source_name", spider.name),
            started_at=timezone.now(),
            status=ScrapeRunStatus.RUNNING,
        )

    def _save_event(self, item: dict[str, Any]) -> bool:
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
        return created

    def _finish_scrape_run(self) -> None:
        error_message = ""
        status = ScrapeRunStatus.SUCCESS

        if getattr(self, "crawler", None):
            stats = self.crawler.stats.get_stats()
            error_count = stats.get("log_count/ERROR", 0)

            if error_count:
                status = ScrapeRunStatus.PARTIAL
                error_message = f"Scrapy logged {error_count} error(s). Check scraper logs."

        self.run.finished_at = timezone.now()
        self.run.status = status
        self.run.total_found = self.total_found
        self.run.total_created = self.total_created
        self.run.total_updated = self.total_updated
        self.run.error_message = error_message
        self.run.save()
