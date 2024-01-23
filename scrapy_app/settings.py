# Scrapy settings for CourtUsCrawler project
# For simplicity, this file contains only settings considered important or commonly used. Documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html
import os
from datetime import date

# folders
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))    # root project dir
LOG_DIR = os.path.join(PROJECT_DIR, '_etc', 'logs')

INPUT_CSV_PATH = os.path.join(PROJECT_DIR, 'input.csv')
FILES_DIR = os.path.join(PROJECT_DIR, 'files')


# crawling settings
MAX_COMPANIES = None    # crawl all input.csv
# MAX_COMPANIES = 80    # crawl firxt X rows from input.csv

DAYS_BACK = 10


# ENABLING CACHE SPEEDS UP THE FIRST CRAWLING (UNTIL CAPTCHA FACED), BUT MAY LEAD TO UNSOLVABLE CAPTCHAS
USE_CACHE = False
CACHE_JSON_PATH = os.path.join(PROJECT_DIR, '_etc', 'session_cache.json')


# captcha settings
TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'

TWO_CAPTCHA_SITE_KEY = '6LdiezYUAAAAAGJqdPJPP7mAUgQUEJxyLJRUlvN6'   # don't change
MAX_CAPTCHA_RETRIES = 10


# proxy settings
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
    # 'scrapy_app.proxies.proxymesh.ProxyMeshMiddleware': 110,      # uncomment for Proxymesh
    # 'scrapy_app.proxies.smartproxy.SmartProxyMiddleware': 100,    # uncomment for Smartproxy
}

# # Proxymesh Settings
# PROXYMESH_URL = 'http://us-il.proxymesh.com:31280'
# PROXYMESH_TIMEOUT = 60    # Proxymesh request timeout

# # Smartproxy Settings
# SMARTPROXY_USER = 'spdd59c579'
# SMARTPROXY_PASSWORD = 'password'
# SMARTPROXY_ENDPOINT = 'us.smartproxy.com'
# SMARTPROXY_PORT = '10000'


# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# standard settings
BOT_NAME = "CourtUsCrawler"
SPIDER_MODULES = ["scrapy_app.spiders"]


# logging settings
import logging
from .utils.logging import create_console_handler, create_file_handler, DEFAULT_LOG_FORMAT, DATE_FORMAT, reload_logging

# setup Console logging using standard Scrapy log
LOG_LEVEL = logging.INFO

# setup File logging
# in Scrapy 2.11, file_mode='w' doesn't work properly, so only 'a' for now
logging.basicConfig(
    handlers=[
        # create_console_handler(level=logging.INFO),    # scrapy handles it based on LOG_LEVEL
        # create_file_handler(level=logging.DEBUG, file_name='debug.log', dir_name=LOG_DIR, file_mode='w'),
        create_file_handler(level=logging.INFO, file_name=f'log_{date.today().isoformat()}.log', dir_name=LOG_DIR, file_mode='w')
    ],
    format=DEFAULT_LOG_FORMAT,
    datefmt=DATE_FORMAT,
    level=logging.DEBUG     # not used, overriden in handlers
)


# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
