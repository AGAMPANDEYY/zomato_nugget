import logging
import sys
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crawler_scraper.crawler.crawler_orchestrator import run_crawling_pipeline
from crawler_scraper.crawler.router import process_urls
from crawler_scraper.tests.test_crawl4ai import *

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("crawler.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_crawled_urls() -> list:
    
    file_path = os.path.join(
        os.path.dirname(__file__),
         "crawler", "output", "crawled_urls.json"
    )
    with open(file_path, 'r') as f:
        urls = json.load(f)
    return urls


async def crawler_scraper_main():
    setup_logging()
    logging.info("Starting the web crawler pipeline...")

    # 1) Crawl & discover URLs, write to JSON
    url_list = await run_crawling_pipeline()
    """
    url_list will be list of dictionary
    [{"restaurant_name":xxxx, "url":xxxxxx},{},....]
    [
    {"restaurant_name":...., {url, markdown, metadata..etc}},
    {},.......    
    ]
    """
    logging.info(f"Discovered {len(url_list)} URLs, saved to output file.")

    logging.info(f"saving the url list")
    """
    processed_combined_data=await process_urls(url_list)

    logging.info(f"Scarping complete")
    out_path = os.path.join(
        os.path.dirname(__file__),
        "..", "crawler", "output", "processed_data.json"
    )
    with open(out_path, 'w') as f:
        json.dump(processed_combined_data, f, indent=2)
    logging.info(f"Results saved to {out_path}")
    """
    return url_list