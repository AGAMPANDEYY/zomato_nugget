
# router.py
import logging
from crawler_scraper.crawler.middleware.ethics_check import *
from tenacity import retry, stop_after_attempt, wait_exponential
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapegraphai.graphs import SmartScraperGraph
from crawler_scraper.scrapers.bs4_fetcher import BS4Fetcher
from crawler_scraper.scrapers.selenium_fetcher import SeleniumFetcher
from crawler_scraper.scrapers.crawl4ai_fetcher import Crawl4AIFetcher
from crawler_scraper.scrapers.scrapegraphai_fetcher import ScrapeGraphAIFetcher
from crawler_scraper.cleaner.cleaner import clean_data, normalize
import asyncio
import random
import json
import os
# --- Configuration ---

# Polite crawling
DOWNLOAD_DELAY = 2  # seconds 

# Tenacity retry wrapper
def retry_policy():
    return dict(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30)
    )


async def test_proxy(proxy: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://httpbin.org/ip", proxy=proxy, timeout=5) as response:
                return response.status == 200
    except Exception:
        return False

# New: Load free proxies from the JSON file
def load_free_proxies():
    proxy_file = os.path.join(os.path.dirname(__file__), "..", "scrapers", "proxy", "free_proxy2.json")
    with open(proxy_file, 'r') as f:
        # Assuming the JSON file contains a list of proxy objects
        proxies = json.load(f)
    return proxies

# Global list of free proxies loaded once
PROXIES = load_free_proxies()

async def get_valid_proxy(proxies):
    for _ in range(len(proxies)):
        proxy = random.choice(proxies)
        proto = proxy.get("protocol", "http")
        if proto not in ["http", "https"]:
            continue
        proxy_url = f"{proto}://{proxy['ip']}:{proxy['port']}"
        if await test_proxy(proxy_url):
            return proxy_url
    return None  # Fallback to no proxy if none are valid

# Update get_random_proxy to use valid proxies
async def get_random_proxy():
    return await get_valid_proxy(PROXIES)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    # Add more for better rotation and anti-blocking
]


# --- Scraper Router ---
# 1. ScrapeGraphAI for structured data
# 2. Selenium for JS-heavy sites
# 3. Crawl4AI for SPA/JS sites
# 4. Scrapy for multi-page discovery
# 5. BeautifulSoup for simple HTML fetch


#rotate proxy and user agent for each request 

def get_random_user_agent():
    return random.choice(USER_AGENTS)

retry_policy = dict(
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=1, max=10)
)

class ScraperRouter:
    def __init__(self):
        self.fetchers = [
            #("ScrapeGraphAIFetcher", ScrapeGraphAIFetcher),  # output like a JSON
             #("Crawl4AIFetcher", Crawl4AIFetcher),        #markdown output
             ("SeleniumFetcher", SeleniumFetcher),        # needs normalization
            ("BS4Fetcher", BS4Fetcher)             # needs normalization
        ]

    @retry(**retry_policy)
    async def fetch_content(self, url: str) -> tuple[str, str]:
        combined_scrapped_data = {
            #"ScrapeGraphAIFetcher": [], #Since ScrapGraphAI has free tier and gives inssuficient credit issues. Max 1000 requests/month limit for free
            "SeleniumFetcher": [],
            #"Crawl4AIFetcher": [],
            "BS4Fetcher": []
        }
        import logging 
        for fetcher_name, fetcher in self.fetchers:
                try:
                    import logging 
                    logging.debug(f"Attempting {fetcher_name} for {url}")
                    # Call the async fetcher function with the URL
                    content = await fetcher(url, get_random_user_agent())
                    # Crawl4AI will return a dict with Markdown and Media, while others will return a JSON
                    combined_scrapped_data[fetcher_name].append((url, content))

                except Exception as e:
                    logging.info(f"{fetcher_name} failed: {e}")
        
        return combined_scrapped_data
                

async def process_urls(urls):
    router = ScraperRouter()
    
    processed_combined_scrapped_data = {
        #"ScrapeGraphAIFetcher": [],
        "SeleniumFetcher": [],
        #"Crawl4AIFetcher": [],
        "BS4Fetcher": []
    }

    for url in urls:
        await asyncio.sleep(0.1)

        if not is_allowed(url):
            logging.warning(f"Blocked by ethical checks: {url}")
            continue

        try:
            combined_scrapped_data = await router.fetch_content(url)
            # Process each fetcher's data
            for fetcher_name, fetched_data in combined_scrapped_data.items():
                for fetched_url, content in fetched_data:
                    # Only normalize for specific fetchers
                    if fetcher_name in ["SeleniumFetcher", "BS4Fetcher"]:
                        data = normalize(clean_data(content, fetcher_name))
                    else:
                        data = clean_data(content, fetcher_name)

                    processed_combined_scrapped_data[fetcher_name].append((fetched_url,data))
                    logging.info(f"Scraped {fetched_url} using {fetcher_name}")
        
        except Exception as e:
            logging.error(f"Failed {url}: {e}")
            continue
        
    return processed_combined_scrapped_data    
