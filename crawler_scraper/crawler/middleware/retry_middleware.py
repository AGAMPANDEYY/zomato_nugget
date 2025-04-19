from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
def retry_scrape(scraper_func, *args):
    return scraper_func(*args)

