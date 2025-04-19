
"""
Ethical Scraping Checker
Check if scraping is allowed for the given URL by:
1. Checking robots.txt rules
2. Respecting rate limits
3. Validating URL format
"""



from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import aiohttp
import asyncio
from typing import Dict
import time
import logging

class EthicalScrapingChecker:
    def __init__(self):
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self._last_access: Dict[str, float] = {}
        self.rate_limit = 2.0  # seconds between requests to same domain
        self.user_agent = "MyRAGBot/1.0 (responsible scraping bot)"

    async def fetch_robots_txt(self, domain: str) -> RobotFileParser:
        if domain in self._robots_cache:
            return self._robots_cache[domain]

        rp = RobotFileParser()
        robots_url = f"https://{domain}/robots.txt"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        rp.parse(robots_content.splitlines())
                    else:
                        # If no robots.txt, assume everything is allowed
                        rp.allow_all = True
        except Exception as e:
            logging.warning(f"Could not fetch robots.txt for {domain}: {e}")
            rp.allow_all = True

        self._robots_cache[domain] = rp
        return rp

    def respect_rate_limit(self, domain: str) -> bool:
        current_time = time.time()
        if domain in self._last_access:
            time_diff = current_time - self._last_access[domain]
            if time_diff < self.rate_limit:
                return False
        self._last_access[domain] = current_time
        return True

async def is_allowed(url: str) -> bool:
    """
    Check if scraping is allowed for the given URL by:
    1. Checking robots.txt rules
    2. Respecting rate limits
    3. Validating URL format
    """
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False

        checker = EthicalScrapingChecker()
        domain = parsed_url.netloc
        
        # Check robots.txt
        rp = await checker.fetch_robots_txt(domain)
        if not rp.can_fetch(checker.user_agent, parsed_url.path):
            logging.info(f"Blocked by robots.txt: {url}")
            return False

        # Check rate limiting
        if not checker.respect_rate_limit(domain):
            logging.info(f"Rate limited: {url}")
            return False

        # Additional ethical checks
        blocked_patterns = [
            '/private/', '/admin/', '/internal/',
            'login', 'signin', 'account',
            'checkout', 'cart', 'payment'
        ]
        
        if any(pattern in url.lower() for pattern in blocked_patterns):
            logging.info(f"URL contains sensitive pattern: {url}")
            return False

        return True

    except Exception as e:
        logging.error(f"Error checking URL {url}: {e}")
        return False