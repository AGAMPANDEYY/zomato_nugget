from scrapegraphai.graphs import SmartScraperGraph
import json
from dotenv import load_dotenv
import os
import logging

from scrapegraph_py import Client

load_dotenv()

from pydantic import BaseModel, Field



async def ScrapeGraphAIFetcher(url: str) -> str:

        """
        Fetch structured data via ScrapeGraphAI.
        """
        SCRAPEGRAPH_API_KEY=os.getenv("SGAI_API_KEY")
        class RestaurantPydantic(BaseModel):
            """
            Pydantic model for restaurant data.
            """
            name: str
            address: str = Field(default=None, description="Address of the restaurant")
            cuisine: str = Field(default=None, description="Cuisine type")
            rating: float = Field(default=None, description="Rating of the restaurant")
            timing: str = Field(default=None, description="Opening hours")
            menu: list = Field(default_factory=list, description="Menu items")
            
        # 1. Highly structured via ScrapeGraphAI
        try:
            
            client = Client(api_key=SCRAPEGRAPH_API_KEY)

            response = client.smartscraper(
                website_url=url,
                user_prompt="Extract useful information from the restaurant website and the details of the menu items and everything that can help answer every customer query.",
                output_schema=RestaurantPydantic
            )
            result=json.dumps(response['result'], indent=4) 
            client.close()
            logging.info(f"ScrapeGraphAI response for {url}: {result}")
            return result #LLM‑driven extract 
        
        except Exception as e:
            logging.error(f"ScrapeGraphAI failed for {url}: {e}")
            pass  # Skip this URL and try the next fetcher
        
            return None  # If all fetchers fail, return None
