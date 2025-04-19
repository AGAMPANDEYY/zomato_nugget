
# router.py
from crawler.middleware.ethics_check import *
from tenacity import retry, stop_after_attempt, wait_exponential
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapegraphai.graphs import SmartScraperGraph
from scrapers.bs4_fetcher import BS4Fetcher
from scrapers.selenium_fetcher import SeleniumFetcher
from scrapers.crawl4ai_fetcher import Crawl4AIFetcher
from scrapers.scrapegraphai_fetcher import ScrapeGraphAIFetcher
from cleaner.cleaner import clean_data, normalize
import logging
import asyncio
# --- Configuration ---

# Polite crawling
DOWNLOAD_DELAY = 2  # seconds 

# Tenacity retry wrapper
def retry_policy():
    return dict(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30)
    )

# Proxy & UA pools
PROXIES = [
    "http://proxy1:8000", "http://proxy2:8000",  # ...
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)…",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)…",
    # ...
]

# --- Scraper Router ---
# 1. ScrapeGraphAI for structured data
# 2. Selenium for JS-heavy sites
# 3. Crawl4AI for SPA/JS sites
# 4. Scrapy for multi-page discovery
# 5. BeautifulSoup for simple HTML fetch


retry_policy = dict(
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=1, max=10)
)

class ScraperRouter:
    def __init__(self):
        self.fetchers = [
            ScrapeGraphAIFetcher(),
            SeleniumFetcher(),
            Crawl4AIFetcher(),
            BS4Fetcher()
        ]

    @retry(**retry_policy)
    async def fetch_content(self, url: str) -> str:
        for fetcher in self.fetchers:
            try:
                logging.debug(f"Attempting {fetcher.__class__.__name__} for {url}")
                result = fetcher.fetch(url)
                return await result if asyncio.iscoroutine(result) else result
            except Exception as e:
                logging.info(f"{fetcher.__class__.__name__} failed: {e}")
        raise Exception("All fetchers failed")


async def process_urls(urls):
    router = ScraperRouter()
    for url in urls:
        # Add delay between checks
        await asyncio.sleep(0.1)
        
        if not await is_allowed(url):
            logging.warning(f"Blocked by ethical checks: {url}")
            continue
            
        try:
            html = await router.fetch_content(url)
            data = normalize(clean_data(html))
            # save or index...
        except Exception as e:
            logging.error(f"Failed {url}: {e}")