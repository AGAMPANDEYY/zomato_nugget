from scrapegraphai.graphs import SmartScraperGraph
import json

async def ScrapeGraphAIFetcher(url: str) -> str:

        """
        Fetch structured data via ScrapeGraphAI.
        """

        # Define the configuration for the scraping pipeline
        graph_config = {
            "llm": {
                "model": "ollama/llama3.2",
                "model_tokens": 8192
            },
            "verbose": True,
            "headless": False,
        }

        # 1. Highly structured via ScrapeGraphAI
        try:
            # Create the SmartScraperGraph instance
            smart_scraper_graph = SmartScraperGraph(
                prompt="""Extract useful information from the restaurant website and the details of the menu items and everything that
                can help answer every customer query.""",
                source=url,
                config=graph_config
            )

            # Run the pipeline
            result = smart_scraper_graph.run()

            return json.dumps(result, indent=4) # LLM‑driven extract 
        except Exception:
            pass
