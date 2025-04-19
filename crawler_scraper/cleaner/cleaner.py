from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Union

def clean_data(html: str, scraper_type: str) -> str:
    """
    Clean HTML based on scraper type, skip cleaning for Crawl4AI
    """
    if scraper_type in ['Crawl4AIFetcher', 'ScrapeGraphAIFetcher']:
        return html
        
    # Clean HTML from other scrapers
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'iframe', 'noscript']):
        element.decompose()
        
    # Remove hidden elements
    for element in soup.find_all(style=re.compile(r'display:\s*none')):
        element.decompose()
        
    # Clean whitespace and special characters
    text = soup.get_text(separator=' ')
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces
    text = re.sub(r'[\n\r\t]', ' ', text)  # Remove newlines/tabs
    
    return text.strip()



from typing import Dict, Any
import json
import re

def normalize(data: str) -> Dict[Any, Any]:
    """
    Normalize cleaned data into a consistent structure
    """
    try:
        # If it's already JSON (from Crawl4AI/ScrapeGraphAI), parse and return
        if isinstance(data, (dict, list)):
            return data
        if data.strip().startswith('{') or data.strip().startswith('['):
            return json.loads(data)
            
        # For cleaned HTML text, extract structured data
        restaurant_data = {}
        
        # Extract name (usually first prominent text)
        name_match = re.search(r'^([^|•\-]+)', data)
        if name_match:
            restaurant_data['name'] = name_match.group(1).strip()
            
        # Extract menu items (looking for price patterns)
        menu_items = []
        price_pattern = r'(?:₹|Rs\.?)\s*(\d+(?:\.\d{2})?)'
        
        # Split into potential menu items (by price)
        items = re.split(price_pattern, data)
        for i in range(0, len(items)-2, 2):
            item_text = items[i].strip()
            price = items[i+1]
            
            if item_text and price:
                menu_items.append({
                    'item': item_text,
                    'price': float(price)
                })
                
        restaurant_data['menu'] = menu_items
        
        # Extract other common fields
        patterns = {
            'rating': r'(\d+\.?\d*)\s*(?:stars?|★)',
            'cuisine': r'Cuisine:\s*([^•|\n]+)',
            'address': r'Address:\s*([^•|\n]+)',
            'timing': r'(?:Timing|Hours):\s*([^•|\n]+)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, data, re.I)
            if match:
                restaurant_data[field] = match.group(1).strip()
                
        return restaurant_data
        
    except Exception as e:
        raise ValueError(f"Normalization failed: {str(e)}")

