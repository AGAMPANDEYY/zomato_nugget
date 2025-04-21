import json
from typing import Dict
from pathlib import Path

def load_urls() -> Dict[str, dict]:
    """
    Load and construct seed URLs from the JSON configuration file.
    Returns a dictionary where each key is a restaurant name and the value is a dict with the base_url.
    
    Expected output format:
    {
      "swiggy_lucknow_mcdonalds": { "base_url": "https://www.swiggy.com/..." },
      "dominos": { "base_url": "https://pizzaonline.dominos.co.in/..." },
      ...
    }
    """
    # Get the path to seed_urls.json relative to this file.
    json_path = Path(__file__).parent / "seed_urls.json"
    
    with open(json_path, 'r') as f:
        config = json.load(f)
    
    seed_urls = {}
    
    for platform, data in config.items():
        base_url = data.get('base_url')
        if base_url:
            seed_urls[platform] = {"base_url": base_url}
    
    return seed_urls