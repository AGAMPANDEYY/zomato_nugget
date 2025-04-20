"""Fetch dynamic page HTML via Crawl4AI."""

from crawl4ai import AsyncWebCrawler
from crawl4ai import CrawlerRunConfig, CacheMode, BrowserConfig
import logging
import asyncio


async def Crawl4AIFetcher(url: str) -> dict:

    print(f"Fetching data from {url}...")
    browser_cfg = BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=True
        )
    
    crawl_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            css_selector="main.article",
            word_count_threshold=10,
            screenshot=True
        )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        res = await crawler.arun(url, config=crawl_cfg)
    if not res.success:
        raise Exception(f"Crawl4AI failed: {res.error_message}")
    logging.info(f"Crawl4AI response for {url}: {res.markdown}")
    return {'content': res.markdown, 'media': res.media} 

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