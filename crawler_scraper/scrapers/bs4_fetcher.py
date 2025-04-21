
"""Simple HTML fetch via requests with UA & proxy rotation."""
import requests
import random 
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

async def BS4Fetcher(url: str, user_agent) -> str:
    """
    Fetch HTML content using BeautifulSoup with UA & proxy rotation.
    """

    session = requests.Session()
    session.headers['User-Agent'] = user_agent
    #session.proxies.update({"http": proxy, "https": proxy})
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text
