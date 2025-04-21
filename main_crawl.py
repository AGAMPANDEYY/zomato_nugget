import asyncio
import os 
from dotenv import load_dotenv
import datetime
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crawler_scraper.run_crawler_scraper import crawler_scraper_main
from ingestion.datalake import DataLake 

load_dotenv()
# Load environment variables from .env file
CATALOG_NAME = os.getenv("CATALOG_NAME")
WAREHOUSE_PATH = os.getenv("WAREHOUSE_PATH")

async def main():
    # 1. Run the crawler-scraper pipeline to obtain processed_combined_scrapped_data
    url_list = await crawler_scraper_main()
    print("Crawling completed")

if __name__ == "__main__":
    asyncio.run(main())
