import os, random, json


def load_free_proxies():
    proxy_file = os.path.join(os.path.dirname(__file__), "..", "scrapers", "proxy", "free_proxy.json")
    with open(proxy_file, 'r') as f:
        # Assuming the JSON file contains a list of proxy objects
        proxies = json.load(f)
    return proxies

# Global list of free proxies loaded once
PROXIES = load_free_proxies()
def get_random_proxy(max_attempts=10):
    attempts = 0
    while attempts < max_attempts:
        proxy = random.choice(PROXIES)
        proto = proxy.get("protocols", ["http"])[0]
        if proto in ["http", "https"]:
            proxy_url = f"{proto}://{proxy['ip']}:{proxy['port']}"
            try:
                # Lightweight check
                requests.get("https://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url}, timeout=3)
                return proxy_url
            except:
                attempts += 1
    raise Exception("No working proxy found.")


import requests

def test_proxy(proxy_url):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url}, timeout=5)
        print(f"✅ Proxy {proxy_url} works: {response.text}")
    except Exception as e:
        print(f"❌ Proxy {proxy_url} failed: {e}")



test_proxy(get_random_proxy())