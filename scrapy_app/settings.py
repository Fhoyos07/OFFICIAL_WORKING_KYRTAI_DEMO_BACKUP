# Scrapy settings for CourtUsCrawler project
# For simplicity, this file contains only settings considered important or commonly used. Documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html
import os
import logging
from datetime import date
from .utils.logging import create_console_handler, create_file_handler, DEFAULT_LOG_FORMAT, DATE_FORMAT

# folders
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))    # root project dir
LOG_DIR = os.path.join(PROJECT_DIR, '_etc', 'logs')
FILES_DIR = os.path.join(PROJECT_DIR, 'files')
INPUT_CSV_PATH = os.path.join(FILES_DIR, 'input.csv')


# crawling settings
MAX_COMPANIES = None    # crawl all input.csv
# MAX_COMPANIES = 80    # crawl firxt X rows from input.csv

DAYS_BACK = 10


# ENABLING CACHE SPEEDS UP THE FIRST CRAWLING (UNTIL CAPTCHA FACED), BUT MAY LEAD TO UNSOLVABLE CAPTCHAS
USE_CACHE = False
CACHE_JSON_PATH = os.path.join(PROJECT_DIR, '_etc', 'session_cache.json')


# captcha settings
TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'

MAX_CAPTCHA_RETRIES = 10


# Proxymesh Settings
PROXYMESH_ENABLED = False
PROXYMESH_USER = 'madfatcat'
PROXYMESH_PASSWORD = 'password'
PROXYMESH_ENDPOINT = 'nl.proxymesh.com'

# Smartproxy Settings
SMARTPROXY_ENABLED = False
SMARTPROXY_USER = 'spdd59c579'
SMARTPROXY_PASSWORD = 'password'
SMARTPROXY_ENDPOINT = 'us.smartproxy.com'
SMARTPROXY_PORT = '10000'

DOWNLOADER_MIDDLEWARES = {
    # 'scrapy_app.proxies.proxymesh.ProxyMeshMiddleware': 110,    # set PROXYMESH_ENABLED to True to activate
    # 'scrapy_app.proxies.smartproxy.SmartProxyMiddleware': 110,  # set SMARTPROXY_ENABLED to True to activate
}


# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


# standard settings
BOT_NAME = "CourtUsCrawler"
SPIDER_MODULES = ["scrapy_app.spiders"]


# logging settings
def setup_logging():
    if hasattr(setup_logging, "has_been_called"): return

    logging.basicConfig(
        handlers=[
            create_console_handler(level=logging.INFO),
            create_file_handler(level=logging.INFO, file_name=f'log_{date.today().isoformat()}.log', dir_name=LOG_DIR, file_mode='w')
        ],
        format=DEFAULT_LOG_FORMAT,
        datefmt=DATE_FORMAT,
        level=logging.DEBUG  # not used, overriden in handlers
    )
    logging.debug('Init logging')
    setup_logging.has_been_called = True

# Initialize Logging (only once)
setup_logging()

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
