# rag-crawler

                           ┌─────────────────────────────┐
                           │    User starts pipeline      │
                           └────────────┬────────────────┘
                                        ▼
                           ┌─────────────────────────────┐
                           │      orchestrator.py         │
                           └────────────┬────────────────┘
                                        ▼
        ┌────────────────────────────────────────────────────────────────────┐
        │              CRAWLING: Choose between Scrapy ↔ Crawl4AI            │
        └────────────┬───────────────────────────────────────────────────────┘
                     ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │        If known static sitemap → use Scrapy                                 │
    │        If site is messy or semantically deep → use Crawl4AI                 │
    │        Crawl4AI uses GPT to pick only relevant links from the page          │
    └──────────────────────────────────────────────────────────────────────────────┘
                     ▼
        ┌────────────────────────────────────────────────────────────────────┐
        │            SCRAPER ROUTING: Choose based on page type              │
        └────────────┬───────────────────────────────────────────────────────┘
                     ▼
     ┌─────────────┬──────────────┬──────────────┬────────────────────────────┐
     │ BeautifulSoup │ Scrapy Spider │ Selenium       │ ScrapeGraphAI (LLM parsing) │
     └─────────────┴──────────────┴──────────────┴────────────────────────────┘
                     ▼
              Clean → Normalize → Save → Embed → RAG




## Overview
The `rag-crawler` project is a production-ready web crawler and scraper designed to gather restaurant data efficiently. It utilizes various technologies and libraries to ensure robust and scalable data extraction.

## Directory Structure
- **crawler/**: Contains the core functionality for web crawling and scraping.
  - **config/**: Configuration files for the crawler.
  - **urls/**: Seed URLs for initiating the crawling process.
  - **middleware/**: Middleware components for handling requests and responses.
  - **scrapy_spiders/**: Scrapy spiders for static web scraping.
  - **selenium_scraper/**: Selenium-based scrapers for dynamic content.
  - **bs4_scraper/**: Beautiful Soup scrapers for parsing HTML.
  - **output/**: Output files for storing scraped data.

- **tests/**: Unit and integration tests for ensuring code quality and functionality.

- **utils/**: Utility functions and classes used throughout the project.

## Installation
To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Configuration
Configuration settings can be found in `crawler/config/crawler_settings.yaml`. Modify this file to adjust user agents, timeouts, and other parameters as needed.

## Running the Crawler
To start the crawler, execute the following command:

```
python run_crawler.py
```

## Testing
To run the tests, use the following command:

```
pytest tests/
```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.


