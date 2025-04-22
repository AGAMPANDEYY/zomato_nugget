"""
The processed data is in format

{
  "indian_restaurants": [
    {
      "base_url": "https://indiarestaurant.co.in/",
      "fetched": [
        {
          "url": "https://indiarestaurant.co.in/menu.html",
          "data": {
            "metadata": {
              "timestamp": "2025-04-21T18:07:00+05:30",
              "status_code": 200,
              "content_type": "text/html"
            },
            "content": {
              "text": "...cleaned text content...",
              "html": "...raw HTML...",
              "markdown": "...converted markdown..."
            },
            "media": {
              "images": [
                {
                  "src": "assets/images/menu-1/our-speciality-min.webp",
                  "alt": "Our Speciality Menu",
                  "description": "Tandoori platter with naan and dips",
                  "dimensions": {"width": 1200, "height": 800},
                  "format": "webp",
                  "category": "food"
                }
              ],
              "videos": [],
              "documents": [
                {
                  "type": "menu_pdf",
                  "url": "/assets/menus/main.pdf",
                  "pages": 5
                }
              ]
            }
          }
        }
      ],

"""

import os
import json
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from ingestion.datalake import DataLake

# Load environment variables
load_dotenv()
DB_NAME = os.getenv("DB_NAME", "restaurant_data")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "scraped_content")

# Path to the processed JSON file
PROCESSED_FILE = os.path.join(
    os.path.dirname(__file__),
    "crawler_scraper", "crawler", "output", "processed_data.json"
)

def load_processed(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def flatten_rows(processed: dict) -> list[dict]:
    rows = []
    for restaurant, info in processed.items():
        for entry in info.get("fetched", []):
            data = entry.get("data", {})
            metadata = data.get("metadata", {})
            media = data.get("media", {})

            ts_str = metadata.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str)
            except (TypeError, ValueError):
                ts = datetime.now(timezone.utc)

            rows.append({
                "id": f"{restaurant}_{uuid.uuid4()}",
                "restaurant_name": restaurant,
                "scraper_name": "Crawl4AIFetcher",
                "url": entry.get("url", ""),
                "markdown": data.get("markdown", ""),
                "html": data.get("html", ""),
                "media": media,
                "timestamp": ts
            })
    return rows

def main():
    processed = load_processed(PROCESSED_FILE)
    rows = flatten_rows(processed)
    print(f"Prepared {len(rows)} rows for ingestion.")

    dl = DataLake(db_name=DB_NAME, collection_name=COLLECTION_NAME)
    dl.create_collection()
    dl.append_rows(rows)
    print("MongoDB ingestion complete.")

if __name__ == "__main__":
    main()