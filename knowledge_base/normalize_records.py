
import json
import uuid
from datetime import datetime, timezone

async def normalize_records(processed: dict) -> list[dict]:
    flattened = []
    
    for restaurant_name, info in processed.items():
        print(f" Normalizing: {restaurant_name}")
        base_url = info.get("base_url", "")
        
        # Case 1: Direct/Flat document
        if "markdown" in info or "html" in info:
            ts = info.get("timestamp")
            if not isinstance(ts, datetime):
                try:
                    ts = datetime.fromisoformat(ts)
                except:
                    ts = datetime.now(timezone.utc)

            flattened.append({
                "chunk_id": f"{restaurant_name}_{uuid.uuid4()}",
                "scraper_name": info.get("scraper_name", "Unknown"),
                "restaurant_name": restaurant_name,
                "base_url": base_url,
                "url": info.get("url", ""),
                "markdown": info.get("markdown", ""),
                "html": info.get("html", ""),
                "media": info.get("media", {}),
                "timestamp": ts
            })
    return flattened

