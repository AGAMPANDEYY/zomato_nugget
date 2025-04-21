async def SeleniumFetcher(url, user_agent):
    """
    Fetch a webpage using Selenium with rotating user agents and proxies.
    
    Args:
        url (str): The URL of the page to fetch.
    
    Returns:
        str: The HTML content of the fetched page.
    """
    import random
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    import logging


    """Fetch JS page via Selenium with rotating proxy & UA."""
    ua = user_agent
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument(f"--user-agent={ua}")  # rotate UA :contentReference[oaicite:1]{index=1}
   # opts.add_argument(f"--proxy-server={proxy}")  # rotate proxy :contentReference[oaicite:2]{index=2}
    driver = webdriver.Chrome(options=opts)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html