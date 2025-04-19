import sys
import logging
import asyncio
from crawler_scraper.crawler.crawler_orchestrator import run_crawling_pipeline
from crawler_scraper.crawler.router import process_urls

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("crawler.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def crawler_scraper_main():
    setup_logging()
    logging.info("Starting the web crawler pipeline...")

    # 1) Crawl & discover URLs, write to JSON
    url_list = await run_crawling_pipeline()
    logging.info(f"Discovered {len(url_list)} URLs, saved to output file.")

    # 2) Pass URLs into router for scraping
    logging.info("Starting scraping of discovered URLs...")

    processed_combined_scrapped_data= await process_urls(url_list)
    
    logging.info("Scraping complete.")

    return processed_combined_scrapped_data