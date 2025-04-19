import os
import sys
import logging
from crawler.orchestrator import Orchestrator

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("crawler.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logging.info("Starting the web crawler...")
    
    # Initialize the orchestrator
    orchestrator = Orchestrator()
    
    # Run the crawler
    orchestrator.run()

if __name__ == "__main__":
    main()