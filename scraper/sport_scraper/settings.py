BOT_NAME = "sport_scraper"

SPIDER_MODULES = ["sport_scraper.spiders"]
NEWSPIDER_MODULE = "sport_scraper.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 0.5
USER_AGENT = "SportsScheduleAggregator/0.1 (+https://example.com)"

ITEM_PIPELINES = {
    "sport_scraper.pipelines.DjangoEventPipeline": 300,
}

LOG_LEVEL = "INFO"
