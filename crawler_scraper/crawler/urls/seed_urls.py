import json
from typing import List
from pathlib import Path

def load_urls() -> List[str]:
    """
    Load and construct seed URLs from the JSON configuration file
    Returns a list of complete URLs to start crawling from
    """
    # Get the path to seed_urls.json relative to this file
    json_path = Path(__file__).parent / "seed_urls.json"
    
    with open(json_path, 'r') as f:
        config = json.load(f)
    
    seed_urls = []
    
    for platform, data in config.items():
        base_url = data['base_url']
        
        full_url = f"{base_url}"
        seed_urls.append(full_url)
    
    return seed_urls