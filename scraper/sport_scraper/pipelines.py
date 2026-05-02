from __future__ import annotations

import os
import re
import sys
import logging
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import django
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import connection
from django.utils import timezone
from scrapy.exceptions import DropItem


def setup_django() -> None:
    project_root = Path(__file__).resolve().parents[2]
    backend_path = project_root / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    logging.getLogger(__name__).info(
        "DJANGO SETUP START settings_module=%s backend_path=%s",
        os.environ.get("DJANGO_SETTINGS_MODULE"),
        backend_path,
    )
    django.setup()
    logging.getLogger(__name__).info(
        "DJANGO SETUP DONE configured=%s settings_module=%s",
        settings.configured,
        os.environ.get("DJANGO_SETTINGS_MODULE"),
    )


setup_django()

from apps.events.models import Event, EventStatus  # noqa: E402
from apps.scraping_logs.models import ScrapeRun, ScrapeRunStatus  # noqa: E402
from apps.sports.models import Organization, Sport  # noqa: E402


logger = logging.getLogger(__name__)


def _fallback_slug(value: str) -> str:
    """Simple ASCII slug used only if django.utils.text.slugify is unavailable."""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    return re.sub(r"-+", "-", value)


def _safe_database_target() -> str:
    """Describe the active DB target without exposing credentials."""
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        parsed = urlparse(database_url)
        database_name = unquote(parsed.path.lstrip("/")) or "(no database name)"
        return f"DATABASE_URL host={parsed.hostname or '(no host)'} db={database_name}"

    settings = connection.settings_dict
    return (
        "DATABASE_URL not set; "
        f"engine={settings.get('ENGINE')} "
        f"host={settings.get('HOST') or '(local)'} "
        f"db={settings.get('NAME')}"
    )


class DjangoEventPipeline:
    """Persist normalised scraper items through Django ORM into the shared DB."""

    @classmethod
    def from_crawler(cls, crawler: Any) -> "DjangoEventPipeline":
        instance = cls()
        instance.crawler = crawler
        logger.info(
            "DjangoEventPipeline enabled via Scrapy ITEM_PIPELINES=%r",
            crawler.settings.getdict("ITEM_PIPELINES"),
        )
        return instance

    async def open_spider(self) -> None:
        self.total_found = 0
        self.total_created = 0
        self.total_updated = 0
        logger.info("DjangoEventPipeline opening. Active database: %s", _safe_database_target())
        self.run = await sync_to_async(self._create_scrape_run)()

    async def process_item(self, item: dict[str, Any], spider: Any) -> dict[str, Any]:
        self.total_found += 1

        required_fields = [
            "title", "start_date", "source_url",
            "sport_slug", "organization_slug",
        ]
        missing = [f for f in required_fields if not item.get(f)]
        if missing:
            raise DropItem(f"Missing required fields: {', '.join(missing)}")

        # Ensure slug exists (spider sets it, but guard anyway)
        if not item.get("slug"):
            item["slug"] = _fallback_slug(str(item["title"]))[:280]

        logger.info(
            "PIPELINE SAVE START external_id=%r title=%r start_date=%s",
            item.get("external_id") or "",
            item.get("title"),
            item.get("start_date"),
        )
        created, event_id = await sync_to_async(self._save_event)(item)
        if created:
            self.total_created += 1
            result = "created"
        else:
            self.total_updated += 1
            result = "updated"

        logger.info(
            "PIPELINE SAVE DONE external_id=%r title=%r start_date=%s created=%s "
            "result=%s event_id=%s",
            item.get("external_id") or "",
            item.get("title"),
            item.get("start_date"),
            created,
            result,
            event_id,
        )

        return item

    async def close_spider(self) -> None:
        saved_count, saved_2026_count = await sync_to_async(self._future_saved_counts)()
        logger.info(
            "POST-CRAWL saved_count start_date>=%s count=%s saved_2026_count=%s",
            timezone.localdate(),
            saved_count,
            saved_2026_count,
        )
        await sync_to_async(self._finish_scrape_run)()

    # ── Synchronous DB helpers (called via sync_to_async) ─────────────────────

    def _create_scrape_run(self) -> ScrapeRun:
        spider = self.crawler.spider
        return ScrapeRun.objects.create(
            source_name=getattr(spider, "source_name", spider.name),
            started_at=timezone.now(),
            status=ScrapeRunStatus.RUNNING,
        )

    def _save_event(self, item: dict[str, Any]) -> tuple[bool, int]:
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

        # Prefer external_id lookup (stable); fall back to source_url.
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

        try:
            logger.info(
                "PIPELINE UPDATE_OR_CREATE CALL external_id=%r title=%r "
                "start_date=%s lookup=%r",
                external_id,
                item.get("title"),
                item.get("start_date"),
                {
                    key: str(value)
                    for key, value in lookup.items()
                    if key != "organization"
                }
                | {"organization_id": organization.id},
            )
            event, created = Event.objects.update_or_create(defaults=defaults, **lookup)
        except Exception:
            logger.exception(
                "PIPELINE SAVE ERROR during update_or_create external_id=%r title=%r "
                "start_date=%s lookup=%r",
                external_id,
                item.get("title"),
                item.get("start_date"),
                {
                    key: str(value)
                    for key, value in lookup.items()
                    if key != "organization"
                }
                | {"organization_id": organization.id},
            )
            raise
        return created, event.id

    def _future_saved_counts(self) -> tuple[int, int]:
        today = timezone.localdate()
        future_events = Event.objects.filter(start_date__gte=today)
        current_year_future_events = future_events.filter(start_date__year=today.year)
        return future_events.count(), current_year_future_events.count()

    def _finish_scrape_run(self) -> None:
        status = ScrapeRunStatus.SUCCESS
        error_message = ""

        if getattr(self, "crawler", None) and self.crawler.stats:
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
