"""Fetch dynamic page HTML via Crawl4AI."""

from crawl4ai import AsyncWebCrawler
from crawl4ai import CrawlerRunConfig, CacheMode, BrowserConfig
import logging
import asyncio

class Crawl4AIFetcher:
    async def __init__(self, url: str):
        self.url = url

    async def fetch(self):

        print(f"Fetching data from {self.url}...")
  
        async with AsyncWebCrawler(config=self.browser_conf) as crawler:
            res = await crawler.arun(self.url, config=self.crawl_conf)
        if not res.success:
            raise Exception(f"Crawl4AI failed: {res.error_message}")
        return res.markdown 