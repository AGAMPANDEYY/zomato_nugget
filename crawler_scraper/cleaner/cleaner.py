from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Union
from typing import Dict, Any
import json
import re
from pydantic import BaseModel
from typing import List, Optional

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



####### Pydantic Models for Data Validation #######
import re
import json
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, Field
from typing import Any, Dict, List, Optional
import google.generativeai as genai

# --- Schema Definitions ---
class MenuItem(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = Field(default_factory=list)

class Restaurant(BaseModel):
    name: str
    address: Optional[str] = None
    cuisine: Optional[str] = None
    rating: Optional[float] = None
    timing: Optional[str] = None
    menu: List[MenuItem] = Field(default_factory=list)

# --- LLM Fallback Setup ---
import os
GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
json_extractor = genai.GenerativeModel('gemini-1.5-flash')

def llm_extract(html: str) -> Dict[str, Any]:
    """
    Use LLM to extract JSON according to Restaurant schema as a fallback.
    """
    prompt = (
        "Extract the following fields as JSON according to this schema:\n"  
        "name (string), address (string), cuisine (string), rating (float), timing (string), menu (list of {name, description, price, tags})\n"  
        
        f"HTML:\n{html}\n\nJSON:"
    )
    result = json_extractor.generate_content(prompt, max_length=512).text
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        raise ValueError("LLM fallback produced invalid JSON")

### At the end we will have JSON data and markdown from Crawl4AI ###

def normalize(data: Any) -> Dict[str, Any]:
    """
    Normalize scraped data into structured JSON. Uses rule-based parsing first,
    then LLM extraction on validation failure or empty results.
    """
    # 1) Already structured?
    if isinstance(data, (dict, list)):
        return data
    text = data.strip()
    if text.startswith("{") or text.startswith("["):
        return json.loads(text)

    # 2) HTML parsing + rule-based extraction
    soup = BeautifulSoup(data, "html.parser")
    extracted = {
        "name": None,
        "address": None,
        "cuisine": None,
        "rating": None,
        "timing": None,
        "menu": []
    }

    # Name
    h1 = soup.select_one("h1, .restaurant-name")
    if h1:
        extracted["name"] = h1.get_text(strip=True)

    # Address, Cuisine, Timing, Rating via CSS or regex
    field_map = {
        "address": [".address"],
        "cuisine": ["[data-field= cuisine]", "div.cuisine"],
        "timing": [".hours", ".timing"],
    }
    for field, selectors in field_map.items():
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                extracted[field] = el.get_text(strip=True)
                break

    # Rating via regex
    rating_text = soup.get_text()
    m = re.search(r"(\d+\.?\d*)\s*(?:stars?|★)", rating_text)
    if m:
        extracted["rating"] = float(m.group(1))

    # Menu items
    for item_block in soup.select(".menu-item, li.menu-item"):  # adjust selectors
        name_el = item_block.select_one("h3, .item-name")
        price_el = item_block.select_one(".price, span.price")
        desc_el = item_block.select_one(".desc, .description")
        if not (name_el and price_el):
            continue
        name = name_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True)
        price = float(re.sub(r"[^\d.]", "", price_text) or 0)
        desc = desc_el.get_text(strip=True) if desc_el else None
        tags = [t.get_text(strip=True) for t in item_block.select(".tags span")] or []
        extracted["menu"].append({"name": name, "description": desc, "price": price, "tags": tags})

    # 3) Validate and fallback to LLM if needed
    try:
        restaurant = Restaurant(**extracted)
        # If no menu items found, consider fallback
        if not restaurant.menu:
            raise ValidationError("Empty menu", Restaurant)
        return restaurant.dict()
    except (ValidationError, ValueError) as e:
        logging.warning(f"Rule-based normalization incomplete, using LLM fallback: {e}")
        llm_data = llm_extract(data)
        return Restaurant(**llm_data).dict()
