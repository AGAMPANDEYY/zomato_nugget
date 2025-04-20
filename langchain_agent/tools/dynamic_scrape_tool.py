import json
import asyncio
from langchain.agents import Tool
from langchain_community.utilities import SerpAPIWrapper
from crawler_scraper.scrapers.crawl4ai_fetcher import Crawl4AIFetcher
from knowledge_base.normalize_records import normalize_records
from knowledge_base.chunking import chunk_record

searcher = SerpAPIWrapper()

@Tool(name="DynamicScrape", description="Dynamically scrape pages via Crawl4AI for fresh restaurant context")
def dynamic_scrape(query: str) -> str:
    results = searcher.run(query + " site:mcdonalds.com OR pizzahut.com menu spice level")
    urls = [r["link"] for r in json.loads(results)["organic_results"][:3]]

    raw = []
    for url in urls:
        html = Crawl4AIFetcher(url)
        raw.append((url, html))

    normalized = asyncio.run(normalize_records({"Crawl4AIFetcher": raw}))
    chunks = []
    for rec in normalized:
        chunks.extend(chunk_record(rec, strategy="semantic"))

    return "\n\n".join([c["text"] for c in chunks])
