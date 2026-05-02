from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventStatus
from apps.sports.models import Organization, Sport


class EventApiPaginationOrderingTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.sport = Sport.objects.create(name="Judo", slug="judo")
        self.organization = Organization.objects.create(
            name="International Judo Federation",
            slug="ijf",
            website_url="https://www.ijf.org/",
            sport=self.sport,
        )

    def create_event(self, title: str, start_offset: int, **overrides: object) -> Event:
        start_date = timezone.localdate() + timedelta(days=start_offset)
        event_slug = f"{title.lower().replace(' ', '-')}-{start_offset}"
        defaults = {
            "organization": self.organization,
            "sport": self.sport,
            "title": title,
            "slug": event_slug,
            "location": "",
            "country": "France",
            "city": "Paris",
            "start_date": start_date,
            "end_date": start_date,
            "source_url": f"https://www.ijf.org/competition/{event_slug}",
            "external_id": event_slug,
            "status": EventStatus.UPCOMING,
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)

    def response_results(self, response):
        payload = response.json()
        return payload["results"] if "results" in payload else payload

    def event_titles(self) -> list[str]:
        response = self.client.get(reverse("event-list"))
        self.assertEqual(response.status_code, 200)
        return [event["title"] for event in self.response_results(response)]

    def test_events_list_returns_only_upcoming_ordered_by_nearest_date(self) -> None:
        self.create_event("Historical Grand Slam", -365, country="Georgia", city="Tbilisi")
        today_event = self.create_event("Today Grand Slam", 0)
        tomorrow_event = self.create_event("Tomorrow Grand Slam", 1)
        later_event = self.create_event("Later Grand Slam", 30)

        response = self.client.get(reverse("event-list"))

        self.assertEqual(response.status_code, 200)
        results = self.response_results(response)
        self.assertEqual(
            [event["id"] for event in results],
            [today_event.id, tomorrow_event.id, later_event.id],
        )
        self.assertNotIn(
            "Historical Grand Slam",
            [event["title"] for event in results],
        )

    def test_events_archive_returns_past_events_ordered_newest_first(self) -> None:
        self.create_event("Upcoming Grand Slam", 7)
        older_past = self.create_event("Older Past Grand Slam", -365)
        recent_past = self.create_event("Recent Past Grand Slam", -1)

        response = self.client.get(reverse("event-archive"))

        self.assertEqual(response.status_code, 200)
        results = self.response_results(response)
        self.assertEqual(
            [event["id"] for event in results],
            [recent_past.id, older_past.id],
        )
        self.assertNotIn(
            "Upcoming Grand Slam",
            [event["title"] for event in results],
        )

    def test_georgia_related_events_appear_before_international_events(self) -> None:
        self.create_event("Paris Grand Slam", 1, country="France", city="Paris")
        self.create_event("Tbilisi Grand Slam", 10, country="Georgia", city="Tbilisi")
        self.create_event("Tokyo Grand Slam", 2, country="Japan", city="Tokyo")

        self.assertEqual(
            self.event_titles(),
            ["Tbilisi Grand Slam", "Paris Grand Slam", "Tokyo Grand Slam"],
        )

    def test_ordering_within_local_and_international_groups_uses_start_date(self) -> None:
        self.create_event("Tokyo Grand Slam", 8, country="Japan", city="Tokyo")
        self.create_event("Tbilisi Cup", 6, country="Georgia", city="Tbilisi")
        self.create_event("Georgia Open", 3, country="France", city="Paris")
        self.create_event("Paris Grand Slam", 2, country="France", city="Paris")

        self.assertEqual(
            self.event_titles(),
            ["Georgia Open", "Tbilisi Cup", "Paris Grand Slam", "Tokyo Grand Slam"],
        )

    def test_only_upcoming_events_are_returned(self) -> None:
        self.create_event("Past Tbilisi Event", -1, country="Georgia", city="Tbilisi")
        self.create_event("Today Tbilisi Event", 0, country="Georgia", city="Tbilisi")
        self.create_event("Future Paris Event", 1, country="France", city="Paris")

        self.assertEqual(
            self.event_titles(),
            ["Today Tbilisi Event", "Future Paris Event"],
        )
