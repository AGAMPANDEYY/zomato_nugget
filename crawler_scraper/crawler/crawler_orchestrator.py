from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

import asyncio, sys
import logging

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer

import logging
import json
from pathlib import Path
import asyncio
from crawler_scraper.crawler.urls.seed_urls import load_urls
#from crawler.router import choose_scraper
from crawler_scraper.crawler.middleware.ethics_check import is_allowed
from crawler_scraper.cleaner.cleaner import clean_data
from crawler_scraper.cleaner.cleaner import clean_data, normalize

################### Crawl4AI ###################

DOWNLOAD_DELAY=0.1

async def crawl4ai_discover_urls(seed_urls_dict):
    """
    Crawl seed_urls in parallel (up to max_pages), return all internal links discovered.
    """
    # 1. Configure headless Playwright browser
    browser_cfg = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        user_agent="Crawl4AAI"
    )  # controls Chrome launch options :contentReference[oaicite:4]{index=4}

    # 2. Configure crawl: bypass cache, stream=False to collect all results at once
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        max_range=50,
        stream=False
    )  # governs caching, page limits, JS processing :contentReference[oaicite:5]{index=5}

    processed = {}

    # 4. Instantiate the crawler once
    async with AsyncWebCrawler(config=browser_cfg) as crawler:  # :contentReference[oaicite:7]{index=7}
        for restaurant, details in seed_urls_dict.items():
            base_url = details.get("base_url")
            if not base_url or not is_allowed(base_url):
                logging.warning(f"Skipping {restaurant}: {base_url}")
                continue

            # 5. Discover URLs for this restaurant
            await asyncio.sleep(DOWNLOAD_DELAY)
            results = await crawler.arun_many(
                [base_url], config=run_cfg
            )  # :contentReference[oaicite:8]{index=8}

            discovered = set()
            for res in results:
                if not res.success:
                    logging.error(f"{base_url} crawl failed: {res.error_message}")
                    continue
                discovered.add(res.url)
                for link in res.links.get("internal", []):
                    href = link.get("href")
                    if href:
                        discovered.add(href)

            processed[restaurant] = {
                "base_url": base_url,
                "crawled_urls": list(discovered)
            }

    return processed

################ Scrapy ###################


from scrapy.crawler import CrawlerRunner
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from urllib.parse import urlparse
from twisted.internet import reactor, defer
from typing import Set


class ScrapyLinkSpider(CrawlSpider):
    name = "scrapy_link_spider"
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY' : 1.5,

    }

    rules = (
        Rule(
            LinkExtractor(
                allow=r'/(restaurant|menu|food|location)/',
                deny=r'/(login|cart|checkout)/'
            ),
            callback='collect_url',
            follow=True
        ),
    )

    def __init__(self, start_urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.discovered: Set[str] = set()

    def collect_url(self, response):
        self.discovered.add(response.url)

def scrapy_discover(seed_urls: list[str]) -> Set[str]:
    runner = CrawlerRunner()
    results: Set[str] = set()

    @defer.inlineCallbacks
    def crawl():
        # The Deferred resolves to the spider instance
        spider = yield runner.crawl(ScrapyLinkSpider, start_urls=seed_urls)
        results.update(spider.discovered)
        reactor.stop()

    crawl()
    reactor.run()
    return results

################ Scrapy + Crawl4AI ###################

OUTPUT_FILE = Path("crawler_scraper/crawler/output/crawled_urls.json")

async def run_crawling_pipeline():
    seed_urls_dict = load_urls()  # your seed loader

    """
    example of Seed urls 
    {
    "swiggy_lucknow_mcdonalds": {
        "base_url": "https://www.swiggy.com/city/lucknow/mcdonalds-habibullah-estate-road-hazratganj-rest532693"
    }, 
    "swiggy_roorkee_cookhouse":{
        "base_url": "https://www.swiggy.com/city/roorkee/the-cook-house-civil-lines-rest320649?restaurant_id=320649&source=collection&query=North%20Indian"
    },
    
    """
    logging.info(f"Loaded {len(seed_urls_dict)} seed URLs.")

    # 1) Discover via Crawl4AI
    crawl4ai_urls = await crawl4ai_discover_urls(seed_urls_dict)
    logging.info(f"Crawl4AI found {len(crawl4ai_urls)} URLs.")



    """
    Output crawl4ai_urls will look like this below 

    {
    "swiggy_lucknow_mcdonalds": {
        "base_url": "https://www.swiggy.com/city/lucknow/mcdonalds-habibullah-estate-road-hazratganj-rest532693",
        "crawled_urls": [
        "https://www.example.com/page1",
        "https://www.example.com/page2"
        ]
    },
    "swiggy_roorkee_cookhouse": {
        "base_url": "https://www.swiggy.com/city/roorkee/the-cook-house-civil-lines-rest320649?restaurant_id=320649&source=collection&query=North%20Indian",
        "crawled_urls": [
        "https://www.example.com/page3",
        "https://www.example.com/page4"
        ]
    }
    }
    
    """
    # 2) Discover via Scrapy
    #scrapy_urls = scrapy_discover(seed_urls)
    #logging.info(f"Scrapy found {len(scrapy_urls)} URLs.")
    #print(f"Discovered following {scrapy_urls} URLs via Scrapy.")

    # 3) Merge and serialize
    #all_urls = sorted(crawl4ai_urls.union(scrapy_urls))
    all_urls=crawl4ai_urls  #converted unique set URLS to list
    OUTPUT_FILE.write_text(json.dumps(all_urls, indent=2))
    logging.info(f"Wrote {len(all_urls)} URLs to {OUTPUT_FILE}.")

    return all_urls
