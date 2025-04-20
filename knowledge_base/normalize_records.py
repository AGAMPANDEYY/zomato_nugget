
import json

async def normalize_records(raw_data):

    """
    Recursively normalize records from different fetchers into a common format.
    """
    flattened = []
    
    for fetcher, entries in raw_data.items():
        for url, content in entries:
            if fetcher == "Crawl4AIFetcher":
                markdown_text = content.get("markdown", "")
                flattened.append({
                    "source": "crawl4ai",
                    "url": url,
                    "text": markdown_text,
                    "media": content.get("media", [])
                })
            else:
                flattened.append({
                    "source": fetcher.lower(),
                    "url": url,
                    "text": json.dumps(content),  # You can chunk later
                    "metadata": content  # for filtering & queries
                })
    return flattened
