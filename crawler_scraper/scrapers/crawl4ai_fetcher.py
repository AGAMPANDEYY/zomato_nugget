"""Fetch dynamic page HTML via Crawl4AI."""

from crawl4ai import AsyncWebCrawler
from crawl4ai import CrawlerRunConfig, CacheMode, BrowserConfig
import logging
import asyncio

DOWNLOAD_DELAY=5

async def Crawl4AIFetcher(
    crawler: AsyncWebCrawler,
    run_cfg: CrawlerRunConfig,
    url: str
) -> dict:
    """Fetch a single URL using a shared crawler instance."""
    logging.info(f"Fetching: {url}")
    await asyncio.sleep(DOWNLOAD_DELAY)  # polite delay

    # Perform the crawl with your run config
    result = await crawler.arun(url=url, config=run_cfg)
    if not result.success:
        raise RuntimeError(f"Crawl4AI failed: {result.error_message}")

    return {"content": result.markdown, "media": result.media}
    # the output structure is in this format below 
    """
    class CrawlResult(BaseModel):
        url: str
        html: str
        success: bool
        cleaned_html: Optional[str] = None
        media: Dict[str, List[Dict]] = {}
        links: Dict[str, List[Dict]] = {}
        downloaded_files: Optional[List[str]] = None
        screenshot: Optional[str] = None
        pdf : Optional[bytes] = None
        markdown: Optional[Union[str, MarkdownGenerationResult]] = None
        extracted_content: Optional[str] = None
        metadata: Optional[dict] = None
        error_message: Optional[str] = None
        session_id: Optional[str] = None
        response_headers: Optional[dict] = None
        status_code: Optional[int] = None
        ssl_certificate: Optional[SSLCertificate] = None
        dispatch_result: Optional[DispatchResult] = None
...
media (Dict[str, List[Dict]])
What: Contains info about discovered images, videos, or audio. Typically keys: "images", "videos", "audios".
Common Fields in each item:

src (str): Media URL
alt or title (str): Descriptive text
score (float): Relevance score if the crawler’s heuristic found it “important”
desc or description (Optional[str]): Additional context extracted from surrounding text
Usage:

images = result.media.get("images", [])
for img in images:
if img.get("score", 0) > 5:
    print("High-value image:", img["src"])

"""