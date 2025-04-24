import asyncio
import os 
from dotenv import load_dotenv
import datetime
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crawler_scraper.run_crawler_scraper import crawler_scraper_main
from ingestion.datalake import DataLake  # adjust based on your ingestion module's function
from retrieval.hybridrag import *

load_dotenv()
# Load environment variables from .env file
CATALOG_NAME = os.getenv("CATALOG_NAME")
WAREHOUSE_PATH = os.getenv("WAREHOUSE_PATH")

async def main():
    # 1. Run the crawler-scraper pipeline to obtain processed_combined_scrapped_data
    processed_data = await crawler_scraper_main()
    print("Crawling and Scraping complete. Processed data obtained.")

    # 2. Prepare the data to ingest (flatten the dictionary into rows)
    # For example, here we assume one of the scraper's output; modify as needed.
    rows = []
    for scraper, entries in processed_data.items():
        for (u, c) in entries:
            rows.append({
                "scraper_name": scraper,  # e.g., "SeleniumFetcher"
                "url": u,
                "content": c,
                "timestamp": datetime.now().isoformat()
            })
    
    # 3. Create/load the table and push the rows
    datalake = DataLake(catalog_name=CATALOG_NAME, warehouse_path=WAREHOUSE_PATH)
    table = datalake.create_table(datalake.table_identifier)  # This will check if the table exists or create it.
    datalake.append_rows(table, rows)
    print("Data ingestion complete.")

if __name__ == "__main__":
    asyncio.run(main())