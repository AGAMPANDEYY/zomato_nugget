
"""Simple HTML fetch via requests with UA & proxy rotation."""
import requests
import random 
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def BS4Fetcher(url: str) -> str:
    """
    Fetch HTML content using BeautifulSoup with UA & proxy rotation.
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
        # Add more user agents as needed
    ]
    PROXIES = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        # Add more proxies as needed
    ]
    session = requests.Session()
    session.headers['User-Agent'] = random.choice(USER_AGENTS)
    session.proxies.update({"http": random.choice(PROXIES), "https": random.choice(PROXIES)})
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    resp = session.get(url, timeout=15)
    resp.raise_for_status()

    logging.info(f"Fetched {resp.text} from {url}")
    return resp.text
