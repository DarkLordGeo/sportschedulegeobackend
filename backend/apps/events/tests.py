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
        response = self.client.get(reverse("event-list"), follow=True)
        self.assertEqual(response.status_code, 200)
        return [event["title"] for event in self.response_results(response)]

    def filtered_titles(self, **params: str) -> list[str]:
        response = self.client.get(reverse("event-list"), params, follow=True)
        self.assertEqual(response.status_code, 200)
        return [event["title"] for event in self.response_results(response)]

    def test_events_list_returns_only_upcoming_ordered_by_nearest_date(self) -> None:
        self.create_event("Historical Grand Slam", -365, country="Georgia", city="Tbilisi")
        today_event = self.create_event("Today Grand Slam", 0)
        tomorrow_event = self.create_event("Tomorrow Grand Slam", 1)
        later_event = self.create_event("Later Grand Slam", 30)

        response = self.client.get(reverse("event-list"), follow=True)

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

        response = self.client.get(reverse("event-archive"), follow=True)

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

    def test_search_matches_title_city_country_and_organization_name(self) -> None:
        self.create_event("Tbilisi Grand Slam", 1, country="Georgia", city="Tbilisi")
        self.create_event("Paris Masters", 2, country="France", city="Paris")
        other_sport = Sport.objects.create(name="Boxing", slug="boxing")
        other_org = Organization.objects.create(
            name="Georgian Boxing Federation",
            slug="gbf",
            sport=other_sport,
        )
        Event.objects.create(
            organization=other_org,
            sport=other_sport,
            title="Spring Open",
            slug="spring-open",
            location="Tbilisi, Georgia",
            country="Georgia",
            city="Tbilisi",
            start_date=timezone.localdate() + timedelta(days=4),
            end_date=timezone.localdate() + timedelta(days=4),
            source_url="https://example.com/spring-open",
            external_id="spring-open",
            status=EventStatus.UPCOMING,
        )

        self.assertEqual(self.filtered_titles(search="grand slam"), ["Tbilisi Grand Slam"])
        self.assertEqual(self.filtered_titles(search="paris"), ["Paris Masters"])
        self.assertEqual(
            self.filtered_titles(search="Georgian Boxing Federation"),
            ["Spring Open"],
        )

    def test_country_filter_is_case_insensitive(self) -> None:
        self.create_event("Tbilisi Grand Slam", 1, country="Georgia", city="Tbilisi")
        self.create_event("Paris Masters", 2, country="France", city="Paris")

        self.assertEqual(self.filtered_titles(country="georgia"), ["Tbilisi Grand Slam"])

    def test_city_filter_is_case_insensitive(self) -> None:
        self.create_event("Tbilisi Grand Slam", 1, country="Georgia", city="Tbilisi")
        self.create_event("Batumi Cup", 2, country="Georgia", city="Batumi")

        self.assertEqual(self.filtered_titles(city="tbilisi"), ["Tbilisi Grand Slam"])

    def test_sport_filter_uses_slug(self) -> None:
        self.create_event("Tbilisi Grand Slam", 1, country="Georgia", city="Tbilisi")
        boxing = Sport.objects.create(name="Boxing", slug="boxing")
        boxing_org = Organization.objects.create(
            name="World Boxing",
            slug="world-boxing",
            sport=boxing,
        )
        Event.objects.create(
            organization=boxing_org,
            sport=boxing,
            title="Boxing Open",
            slug="boxing-open",
            location="Paris, France",
            country="France",
            city="Paris",
            start_date=timezone.localdate() + timedelta(days=3),
            end_date=timezone.localdate() + timedelta(days=3),
            source_url="https://example.com/boxing-open",
            external_id="boxing-open",
            status=EventStatus.UPCOMING,
        )

        self.assertEqual(self.filtered_titles(sport="boxing"), ["Boxing Open"])

    def test_organization_filter_uses_slug(self) -> None:
        self.create_event("IJF Grand Slam", 1, country="Georgia", city="Tbilisi")
        eju = Organization.objects.create(
            name="European Judo Union",
            slug="eju",
            sport=self.sport,
        )
        Event.objects.create(
            organization=eju,
            sport=self.sport,
            title="EJU Open",
            slug="eju-open",
            location="Prague, Czechia",
            country="Czechia",
            city="Prague",
            start_date=timezone.localdate() + timedelta(days=4),
            end_date=timezone.localdate() + timedelta(days=4),
            source_url="https://example.com/eju-open",
            external_id="eju-open",
            status=EventStatus.UPCOMING,
        )

        self.assertEqual(self.filtered_titles(organization="eju"), ["EJU Open"])

    def test_date_range_filter_uses_start_date(self) -> None:
        self.create_event("Early Event", 1)
        self.create_event("Middle Event", 5)
        self.create_event("Late Event", 10)

        self.assertEqual(
            self.filtered_titles(
                date_from=str(timezone.localdate() + timedelta(days=2)),
                date_to=str(timezone.localdate() + timedelta(days=7)),
            ),
            ["Middle Event"],
        )
