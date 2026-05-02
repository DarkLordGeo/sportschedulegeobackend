from __future__ import annotations

import re
from datetime import date
from typing import Any, Iterable
from urllib.parse import urljoin

import scrapy
from dateutil.parser import parse as parse_date
from django.utils.text import slugify

from sport_scraper.items import EventItem

# Scrape these years. Add more as needed.
CALENDAR_YEARS = ["2025", "2026", "2027"]

# All IJF age-category slugs.
CALENDAR_AGES = ["world_tour", "sen", "jun", "cad", "othr"]

# Month abbreviations that appear in multi-month date ranges like "Feb 27 - Mar 1".
_MONTH_NAME = re.compile(r"[A-Za-z]")


class IjfSpider(scrapy.Spider):
    """
    Scrapes the IJF competition calendar at https://www.ijf.org/calendar.

    Page structure (confirmed by inspection):
    Each calendar page renders a <table> where each <tr> is one event:
      td[0]  date range text  e.g. "February 7 - 8" or "Feb 27 - Mar 1"
      td[1]  empty / flag image
      td[2]  <a href="/competition/ID">Title</a>  plus athlete/nation counts
      td[3]  <a href="/country/xxx">Country, City</a>
      td[4]  action buttons: "Results"/"Draw" or "Judoka"/"Event Info"

    Location is reliably identified by the /country/ link in td[3].
    """

    name = "ijf"
    source_name = "IJF"
    allowed_domains = ["ijf.org", "www.ijf.org"]

    def start_requests(self) -> Iterable[scrapy.Request]:
        """Generate one request per year × age-category combination."""
        for year in CALENDAR_YEARS:
            for age in CALENDAR_AGES:
                url = f"https://www.ijf.org/calendar?year={year}&age={age}"
                yield scrapy.Request(
                    url,
                    callback=self.parse_calendar,
                    cb_kwargs={"year": year, "age": age},
                )

    def parse_calendar(
        self,
        response: scrapy.http.Response,
        year: str,
        age: str,
    ) -> Iterable[EventItem]:
        rows = response.css("table tr")
        self.logger.info(
            f"[{year}/{age}] URL={response.url} | rows found={len(rows)}"
        )

        yielded = 0
        skipped_no_link = 0
        skipped_no_date = 0
        skipped_no_title = 0

        for row in rows:
            # ── 1. Competition link (td[2]: a[href*="/competition/"]) ──────────
            comp_link = row.css("a[href*='/competition/']").get()
            # Skip rows that have no competition link at all (header rows etc.)
            if not comp_link:
                skipped_no_link += 1
                continue

            # Get the first competition link only (athletes/nations links also
            # contain /competition/ so we pick the first anchor in td[2]).
            comp_td = None
            for td in row.css("td"):
                if td.css("a[href*='/competition/']"):
                    # Make sure it's not just the athletes or nations sub-link
                    # by checking whether the td also has meaningful text.
                    comp_td = td
                    break

            if comp_td is None:
                skipped_no_link += 1
                continue

            # The title link is the first /competition/ anchor whose text is
            # not just a number (athletes/nations links have "NNN athletes").
            title = ""
            href = ""
            for anchor in comp_td.css("a[href*='/competition/']"):
                text = self.clean_text(anchor.css("::text").get(""))
                # Skip "488 athletes", "78 nations" etc.
                if text and not re.match(r"^\d+\s+", text):
                    title = text
                    href = anchor.attrib.get("href", "")
                    break

            if not title:
                skipped_no_title += 1
                continue

            source_url = urljoin(response.url, href)
            external_id = self.extract_external_id(source_url)

            # ── 2. Date (td[0]) ───────────────────────────────────────────────
            date_text = self.clean_text(
                " ".join(row.css("td:first-child *::text").getall())
            )
            if not date_text:
                skipped_no_date += 1
                self.logger.debug(f"No date text for: {title}")
                continue

            start_date, end_date = self.parse_date_range(date_text, year)
            if not start_date:
                skipped_no_date += 1
                self.logger.debug(
                    f"Could not parse date '{date_text}' for: {title}"
                )
                continue

            # ── 3. Location (td containing a[href*="/country/"]) ─────────────
            # This is reliably td[3], identified by the /country/ link.
            location = ""
            country = ""
            city = ""
            for td in row.css("td"):
                country_link = td.css("a[href*='/country/']")
                if country_link:
                    location = self.clean_text(
                        " ".join(country_link.css("::text").getall())
                    )
                    city, country = self.split_location(location)
                    break

            # ── 4. Build and yield item ───────────────────────────────────────
            item = EventItem()
            item["sport_slug"] = "judo"
            item["sport_name"] = "Judo"
            item["organization_slug"] = "ijf"
            item["organization_name"] = "International Judo Federation"
            item["organization_website_url"] = "https://www.ijf.org/"
            item["title"] = title
            item["slug"] = slugify(title)[:280]
            item["location"] = location
            item["country"] = country
            item["city"] = city
            item["start_date"] = start_date
            item["end_date"] = end_date
            item["source_url"] = source_url
            item["external_id"] = external_id
            item["status"] = "unknown"

            self.logger.info(
                f"[{year}/{age}] YIELD: '{title}' | {start_date}"
                f"{f' → {end_date}' if end_date else ''}"
                f" | {location or '(no location)'}"
            )
            yielded += 1
            yield item

        self.logger.info(
            f"[{year}/{age}] DONE: yielded={yielded} "
            f"skipped(no_link={skipped_no_link}, "
            f"no_date={skipped_no_date}, no_title={skipped_no_title})"
        )

    # ── Date parsing ──────────────────────────────────────────────────────────

    def parse_date_range(
        self,
        value: str,
        default_year: str = "",
    ) -> tuple[date | None, date | None]:
        """
        Handle the variety of date formats IJF uses:
          "February 7 - 8"          → same-month range
          "Feb 27 - Mar 1"          → cross-month range
          "March 20 - 22"           → same-month range
          "August 23"               → single day
          "Oct 4 - 10"              → same-month range
          "November 1 - 3"          → same-month range
        """
        value = self.clean_text(value)
        if not value:
            return None, None

        # Split on " - " or " – " or " — "
        parts = re.split(r"\s*[-–—]\s*", value, maxsplit=1)
        start_str = parts[0].strip()
        end_str = parts[1].strip() if len(parts) > 1 else ""

        # Append year if missing
        if default_year and default_year not in start_str:
            start_str = f"{start_str} {default_year}"

        if end_str:
            # If end_str is just a bare number like "8" or "22", it's the
            # end day in the same month as start.
            if re.fullmatch(r"\d{1,2}", end_str):
                # Extract month name from start
                month_match = re.search(r"[A-Za-z]+", start_str)
                if month_match:
                    end_str = f"{month_match.group(0)} {end_str}"

            # Append year if missing
            if default_year and default_year not in end_str:
                end_str = f"{end_str} {default_year}"

        start_date = self.parse_date_value(start_str)
        end_date = self.parse_date_value(end_str) if end_str else None

        # Sanity: end_date must not be before start_date
        if start_date and end_date and end_date < start_date:
            end_date = None

        return start_date, end_date

    def parse_date_value(self, value: Any) -> date | None:
        if not value:
            return None
        try:
            return parse_date(str(value), fuzzy=True).date()
        except (TypeError, ValueError, OverflowError):
            return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def split_location(self, location: str) -> tuple[str, str]:
        """
        IJF location format: "Country, City"  (e.g. "Georgia, Tbilisi").
        Returns (city, country).
        """
        parts = [p.strip() for p in location.split(",") if p.strip()]
        if len(parts) >= 2:
            # country = first part, city = everything after first comma
            country = parts[0]
            city = ", ".join(parts[1:])
            return city, country
        if parts:
            return "", parts[0]
        return "", ""

    def extract_external_id(self, source_url: str) -> str:
        match = re.search(r"/competition/(\d+)", source_url)
        return match.group(1) if match else ""

    def clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()