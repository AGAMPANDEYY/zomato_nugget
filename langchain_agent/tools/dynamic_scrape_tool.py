import json
import asyncio
from langchain_core.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from crawler_scraper.tests.test_crawl4ai import Crawl4AIFetcher
from knowledge_base.normalize_records import normalize_records
from knowledge_base.chunking import chunk_record
import os 
from dotenv import load_dotenv
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)

load_dotenv()


searcher = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))

@tool("DynamicScrape", description="Dynamically scrape pages via Crawl4AI for fresh restaurant context")
async def dynamic_scrape(query: str) -> str:
  
    resp = searcher.results(query)  

    organic = resp.get("organic_results", [])  
 
    urls = [r.get("link") for r in organic[:3] if "link" in r]  
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
    
    raw = []
    #5. Open one crawler session for ALL restaurants
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
      for url in urls:
            raw = await Crawl4AIFetcher(crawler, run_cfg, url)
            raw.append((raw['markdown']))

    normalized = asyncio.run(normalize_records({"Crawl4AIFetcher": raw}))
    chunks = []
    for rec in normalized:
        chunks.extend(chunk_record(rec, strategy="semantic"))

    return "\n\n".join([c["text"] for c in chunks])
