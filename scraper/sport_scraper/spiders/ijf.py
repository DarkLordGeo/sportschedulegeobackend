from __future__ import annotations

import re
from datetime import date
from typing import Any, Iterable
from urllib.parse import urljoin

import scrapy
from dateutil.parser import parse as parse_date
from django.utils.text import slugify

from sport_scraper.items import EventItem

CALENDAR_YEARS = ["2025", "2026", "2027"]
CALENDAR_AGES = ["world_tour", "sen", "jun", "cad", "othr"]


class IjfSpider(scrapy.Spider):
    name = "ijf"
    source_name = "IJF"
    allowed_domains = ["ijf.org", "www.ijf.org"]

    def start_requests(self) -> Iterable[scrapy.Request]:
        """Generate requests for each year + category combination."""
        for year in CALENDAR_YEARS:
            for age in CALENDAR_AGES:
                url = f"https://www.ijf.org/calendar?year={year}&age={age}"
                yield scrapy.Request(url, callback=self.parse_calendar)

    def parse_calendar(self, response: scrapy.http.Response) -> Iterable[EventItem]:
        """
        Parse the IJF calendar page.
        Events are rendered in an HTML table. Each row contains:
          - Date cell: e.g. "February  7 - 8"
          - Empty cell (flag/icon)
          - Competition link: <a href="/competition/3131">Paris Grand Slam 2026</a>
          - Athletes/nations info
          - Location: "France, Paris"
        """
        rows = response.css("table tr")
        self.logger.info(f"Found {len(rows)} table rows on {response.url}")

        for row in rows:
            # Date is in first <td>
            date_text = " ".join(row.css("td:first-child *::text").getall()).strip()
            if not date_text:
                continue

            # Competition link
            comp_link = row.css("td a[href*='/competition/']")
            if not comp_link:
                continue

            title = self.clean_text(comp_link.css("::text").get(""))
            href = comp_link.attrib.get("href", "")
            source_url = urljoin(response.url, href)

            if not title or not source_url:
                continue

            # Location — last <td> typically contains "Country, City"
            tds = row.css("td")
            location = ""
            if len(tds) >= 2:
                # Try last td for location
                location = self.clean_text(" ".join(tds[-1].css("*::text").getall()))
                # If it looks like athlete count or something weird, skip
                if re.search(r"\d+\s+athletes", location, re.IGNORECASE):
                    location = ""

            # Extract year from URL params for date parsing context
            year_match = re.search(r"year=(\d{4})", response.url)
            year = year_match.group(1) if year_match else ""

            start_date, end_date = self.parse_date_range(date_text, year)
            if not start_date:
                self.logger.debug(f"Could not parse date '{date_text}' for {title}")
                continue

            external_id = self.extract_external_id(source_url)
            item = self.build_item(
                title=title,
                start_date=start_date,
                end_date=end_date,
                location=location,
                source_url=source_url,
                external_id=external_id,
            )
            self.logger.info(f"Scraped: {title} | {start_date} | {location}")
            yield item

    def build_item(
        self,
        *,
        title: str,
        start_date: date,
        source_url: str,
        end_date: date | None = None,
        location: str = "",
        external_id: str = "",
    ) -> EventItem:
        city, country = self.split_location(location)
        item = EventItem()
        item["sport_slug"] = "judo"
        item["sport_name"] = "Judo"
        item["organization_slug"] = "ijf"
        item["organization_name"] = "International Judo Federation"
        item["organization_website_url"] = "https://www.ijf.org/"
        item["title"] = self.clean_text(title)
        item["location"] = self.clean_text(location)
        item["country"] = country
        item["city"] = city
        item["start_date"] = start_date
        item["end_date"] = end_date
        item["source_url"] = source_url
        item["external_id"] = external_id
        item["status"] = "unknown"
        return item

    def parse_date_range(self, value: str, default_year: str = "") -> tuple[date | None, date | None]:
        value = self.clean_text(value)
        if not value:
            return None, None

        # Split on "to", "-", "–", "—" surrounded by spaces
        parts = re.split(r"\s+[-–—]\s+", value, maxsplit=1)
        start_str = parts[0].strip()
        end_str = parts[1].strip() if len(parts) > 1 else ""

        # Append year if missing
        if default_year:
            if default_year not in start_str:
                start_str = f"{start_str} {default_year}"

            if end_str:
                # Handle bare day number like "8" — prepend month from start
                if re.fullmatch(r"\d{1,2}", end_str):
                    month_match = re.search(r"[A-Za-z]+", start_str)
                    if month_match:
                        end_str = f"{month_match.group(0)} {end_str}"
                if default_year not in end_str:
                    end_str = f"{end_str} {default_year}"

        start_date = self.parse_date_value(start_str)
        end_date = self.parse_date_value(end_str) if end_str else None
        return start_date, end_date

    def parse_date_value(self, value: Any) -> date | None:
        if not value:
            return None
        try:
            return parse_date(str(value), fuzzy=True).date()
        except (TypeError, ValueError, OverflowError):
            return None

    def split_location(self, location: str) -> tuple[str, str]:
        """
        IJF location format is typically "Country, City".
        Returns (city, country).
        """
        parts = [p.strip() for p in location.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-1], parts[0]   # city=last, country=first
        return "", parts[0] if parts else ""

    def extract_external_id(self, source_url: str) -> str:
        match = re.search(r"/competition/(\d+)", source_url)
        return match.group(1) if match else ""

    def clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()