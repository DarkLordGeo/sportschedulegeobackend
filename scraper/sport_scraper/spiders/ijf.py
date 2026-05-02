from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Iterable
from urllib.parse import urljoin

import scrapy
from dateutil.parser import parse as parse_date
from django.utils.text import slugify

from sport_scraper.items import EventItem


class IjfSpider(scrapy.Spider):
    name = "ijf"
    source_name = "IJF"
    allowed_domains = ["ijf.org", "www.ijf.org"]
    start_urls = ["https://www.ijf.org/calendar"]

    def parse(self, response: scrapy.http.Response) -> Iterable[EventItem | scrapy.Request]:
        yield from self.parse_json_ld_events(response)

        # TODO: Inspect the current IJF calendar markup and replace these broad
        # candidate selectors with exact, tested selectors for event cards/rows.
        candidate_events = response.css("tr[data-event-row-link], [data-event], .event, .calendar-event, article")
        for event_node in candidate_events:
            item = self.parse_event_node(event_node, response)
            if item:
                yield item

        # TODO: If the official calendar paginates or lazy-loads events, add
        # pagination/API request discovery here after confirming the live page.
        for href in response.css("a::attr(href)").getall():
            if "/calendar" in href and href != response.url:
                absolute_url = urljoin(response.url, href)
                if absolute_url != response.url:
                    yield response.follow(absolute_url, callback=self.parse)

    def parse_json_ld_events(self, response: scrapy.http.Response) -> Iterable[EventItem]:
        for script in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue
            nodes = data if isinstance(data, list) else [data]
            for node in self.flatten_json_ld(nodes):
                if node.get("@type") not in {"Event", "SportsEvent"}:
                    continue
                title = self.clean_text(node.get("name"))
                start_date = self.parse_date_value(node.get("startDate"))
                if not title or not start_date:
                    continue
                source_url = node.get("url") or response.url
                location = node.get("location")
                location_name = ""
                if isinstance(location, dict):
                    location_name = self.clean_text(location.get("name"))
                elif isinstance(location, str):
                    location_name = self.clean_text(location)

                yield self.build_item(
                    title=title,
                    start_date=start_date,
                    end_date=self.parse_date_value(node.get("endDate")),
                    location=location_name,
                    source_url=urljoin(response.url, source_url),
                    external_id=self.extract_external_id(source_url),
                )

    def parse_event_node(
        self,
        event_node: scrapy.selector.Selector,
        response: scrapy.http.Response,
    ) -> EventItem | None:
        title = self.first_text(
            event_node,
            [
                "td[data-t='Name'] a.event-link-title::text",
                "[data-title]::attr(data-title)",
                ".event-title::text",
                ".title::text",
                "h2::text",
                "h3::text",
                "a::text",
            ],
        )
        source_url = event_node.attrib.get("data-event-row-link")
        if not source_url:
            source_url = self.first_text(
                event_node,
                ["a::attr(href)", "[data-url]::attr(data-url)", "[data-href]::attr(data-href)"],
            )

        date_texts = event_node.css("td[data-t='Date'] *::text").getall()
        date_text = " ".join(date_texts).strip() if date_texts else ""
        if not date_text:
            date_text = self.first_text(
                event_node,
                [
                    "time::attr(datetime)",
                    "[data-date]::attr(data-date)",
                    ".date::text",
                    ".event-date::text",
                ],
            )

        if not title or not source_url or not date_text:
            self.logger.debug(f"Skipping node, missing data. title: {bool(title)}, url: {bool(source_url)}, date: {bool(date_text)}")
            return None

        year_match = re.search(r"\b(20\d\d)\b", title)
        year = year_match.group(1) if year_match else ""
        start_date, end_date = self.parse_date_range(date_text, year)

        if not start_date:
            self.logger.debug(f"Skipping node, could not parse start_date from: {date_text}")
            return None

        loc_texts = event_node.css("td[data-t='Location'] *::text").getall()
        location = " ".join(loc_texts).strip() if loc_texts else ""
        if not location:
            location = self.first_text(
                event_node,
                [
                    "[data-location]::attr(data-location)",
                    ".location::text",
                    ".event-location::text",
                    ".place::text",
                ],
            )

        absolute_source_url = urljoin(response.url, source_url)
        item = self.build_item(
            title=title,
            start_date=start_date,
            end_date=end_date,
            location=location,
            source_url=absolute_source_url,
            external_id=self.extract_external_id(absolute_source_url),
        )
        self.logger.info(f"Extracted event: {item['title']} - {item['start_date']}")
        return item

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
        item["slug"] = slugify(item["title"])[:280]
        item["location"] = self.clean_text(location)
        item["country"] = country
        item["city"] = city
        item["start_date"] = start_date
        item["end_date"] = end_date
        item["source_url"] = source_url
        item["external_id"] = external_id
        item["status"] = "unknown"
        return item

    def flatten_json_ld(self, nodes: list[Any]) -> Iterable[dict[str, Any]]:
        for node in nodes:
            if isinstance(node, dict):
                graph = node.get("@graph")
                if isinstance(graph, list):
                    yield from self.flatten_json_ld(graph)
                else:
                    yield node

    def parse_date_range(self, value: str, default_year: str = "") -> tuple[date | None, date | None]:
        value = self.clean_text(value)
        if not value:
            return None, None
        parts = re.split(r"\s+(?:to|-|–|—)\s+", value, maxsplit=1)
        
        start_str = parts[0]
        end_str = parts[1] if len(parts) > 1 else ""

        if default_year:
            if default_year not in start_str:
                start_str = f"{start_str} {default_year}"
            
            if end_str:
                if re.fullmatch(r"\d+", end_str.strip()):
                    month_match = re.search(r"[a-zA-Z]+", parts[0])
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
        parts = [part.strip() for part in self.clean_text(location).split(",") if part.strip()]
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return "", parts[0] if parts else ""

    def extract_external_id(self, source_url: str) -> str:
        match = re.search(r"/(?:competition|event|calendar)/(\d+)", source_url)
        return match.group(1) if match else ""

    def first_text(self, selector: scrapy.selector.Selector, css_selectors: list[str]) -> str:
        for css_selector in css_selectors:
            value = selector.css(css_selector).get()
            if value:
                return self.clean_text(value)
        return ""

    def clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()
