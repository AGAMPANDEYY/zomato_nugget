import logging
logging.basicConfig(filename='logs/crawl.log', level=logging.INFO)

def log_warning(msg): logging.warning(msg)
def log_error(msg): logging.error(msg)
def log_info(msg): logging.info(msg)
