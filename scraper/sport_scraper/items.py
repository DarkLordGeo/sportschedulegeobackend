from __future__ import annotations

import scrapy


class EventItem(scrapy.Item):
    sport_slug = scrapy.Field()
    sport_name = scrapy.Field()
    organization_slug = scrapy.Field()
    organization_name = scrapy.Field()
    organization_website_url = scrapy.Field()
    title = scrapy.Field()
    location = scrapy.Field()
    country = scrapy.Field()
    city = scrapy.Field()
    start_date = scrapy.Field()
    end_date = scrapy.Field()
    source_url = scrapy.Field()
    external_id = scrapy.Field()
    status = scrapy.Field()
