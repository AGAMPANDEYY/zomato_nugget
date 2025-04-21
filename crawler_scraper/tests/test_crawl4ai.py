import os
import json
import logging
import random
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
import os
import sys

# Insert the project root directory into sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from crawler_scraper.crawler.middleware.ethics_check import is_allowed
from crawler_scraper.cleaner.cleaner import clean_data

# --- Configuration ---
DOWNLOAD_DELAY = 0.1  # seconds between requests

# Load proxies once
def load_free_proxies():
    proxy_path = os.path.join(
        os.path.dirname(__file__),
        "..", "scrapers", "proxy", "free_proxy2.json"
    )
    with open(proxy_path, 'r') as f:
        return json.load(f)

PROXIES = load_free_proxies()

def get_random_proxy():
    p = random.choice(PROXIES)
    proto = p.get("protocols", ["http"])[0]
    return f"{proto}://{p['ip']}:{p['port']}"

def get_random_user_agent():
    UAS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
        # ... more UAs
    ]
    return random.choice(UAS)

async def Crawl4AIFetcher(
    crawler: AsyncWebCrawler,
    run_cfg: CrawlerRunConfig,
    url: str
) -> dict:
    """Fetch a single URL using a shared crawler instance."""
    logging.info(f"Fetching: {url}")
    await asyncio.sleep(DOWNLOAD_DELAY)  # polite delay

    # Perform the crawl with your run config
    result = await crawler.arun(url=url, config=run_cfg)
    if not result.success:
        raise RuntimeError(f"Crawl4AI failed: {result.error_message}")

    return {"url":result.url,"markdown": result.markdown,"html": result.html ,"media": result.media}

async def main():
    # Load URLs
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..", "crawler", "output", "crawled_urls.json"
    )
    with open(file_path, 'r') as f:
        urls_dict = json.load(f)
    logging.info(f"Loaded {len(urls_dict)} URLs")  # :contentReference[oaicite:9]{index=9}

    # Shared browser configuration with stability flags
    browser_cfg = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True,
        extra_args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-browser-side-navigation",
            "--ignore-certificate-errors"
        ],
    )  # :contentReference[oaicite:10]{index=10}

    # Shared run configuration
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True
    ) 
       # 4. Prepare output structure
    processed = {}

    # 5. Open one crawler session for ALL restaurants
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for restaurant, details in urls_dict.items():
            base = details.get("base_url")
            urls = details.get("crawled_urls", [])
            logging.info(f"[{restaurant}] {len(urls)} URLs to scrape")

            results = []
            for url in urls:
                if not is_allowed(url):
                    logging.warning(f"    ✗ Blocked by ethical checks: {url}")
                    continue
                try:
                    raw = await Crawl4AIFetcher(crawler, run_cfg, url)
                    cleaned = clean_data(raw, "Crawl4AIFetcher")
                    results.append({"url": url, "data": cleaned})
                    logging.info(f"    ✓ Scraped {url}")
                except Exception as e:
                    logging.error(f"    ✗ Failed {url}: {e}")

            processed[restaurant] = {
                "base_url": base,
                "fetched": results
            }

    # Save results
    out_path = os.path.join(
        os.path.dirname(__file__),
        "..", "crawler", "output", "processed_data.json"
    )
    with open(out_path, 'w') as f:
        json.dump(processed, f, indent=2)
    logging.info(f"Results saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())  # single entrypoint :contentReference[oaicite:13]{index=13}
