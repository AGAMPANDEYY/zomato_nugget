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
import os, json, uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

from ingestion.datalake import DataLake

# Load .env
load_dotenv()
CATALOG_NAME = os.getenv("CATALOG_NAME", "local_datalake")

PROCESSED_FILE = os.path.join(
    os.path.dirname(__file__),
    "crawler_scraper", "crawler", "output", "processed_data.json"
)

def load_processed(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

def flatten_rows(processed: dict) -> list[dict]:
    rows = []
    for restaurant, info in processed.items():
        for entry in info.get("fetched", []):
            data     = entry["data"]
            ts_str   = data.get("metadata", {}).get("timestamp")
            # parse ISO‐8601 into a timezone-aware datetime
            try:
                ts = datetime.fromisoformat(ts_str)
            except (TypeError, ValueError):
                ts = datetime.now(timezone.utc)   # fallback :contentReference[oaicite:7]{index=7}

            rows.append({
                "id":           f"{restaurant}_{uuid.uuid4()}",
                "scraper_name": "Crawl4AIFetcher",
                "url":          entry["url"],
                "markdown":     data.get("markdown", ""),
                "html":         data.get("html", ""),
                "media":        json.dumps(data.get("media", {})),
                "timestamp":    ts
            })
    return rows

def main():
    processed = load_processed(PROCESSED_FILE)
    rows      = flatten_rows(processed)
    print(f"Prepared {len(rows)} rows for ingestion.")

    dl    = DataLake(catalog_name=CATALOG_NAME)
    table = dl.create_table()          # no args now
    dl.append_rows(table, rows)
    print("💾 Iceberg ingestion complete.")

if __name__ == "__main__":
    main()
