# Scrapy settings for CourtUsCrawler project
# For simplicity, this file contains only settings considered important or commonly used. Documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html
import logging
from datetime import date
from config.settings import BASE_DIR
from utils.logging import create_console_handler, create_file_handler, DEFAULT_LOG_FORMAT, DATE_FORMAT

# folders
ETC_DIR = BASE_DIR / '_etc'
LOG_DIR = ETC_DIR / 'logs'
HTML_DEBUG_DIR = ETC_DIR / 'html'
FILES_DIR = BASE_DIR / 'files'       # root dir for csvs, input and pdfs
INPUT_CSV_PATH = FILES_DIR / 'input.csv'


# crawling settings
DAYS_BACK = 14
MAX_COMPANIES = None    # crawl all input.csv
# MAX_COMPANIES = 70    # crawl first X rows from input.csv


# captcha settings
TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
MAX_CAPTCHA_RETRIES = 20


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
    # 'scraping_service.proxies.proxymesh.ProxyMeshMiddleware': 110,    # set PROXYMESH_ENABLED to True to activate
    # 'scraping_service.proxies.smartproxy.SmartProxyMiddleware': 110,  # set SMARTPROXY_ENABLED to True to activate
}


# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


# standard settings
BOT_NAME = "CourtUsCrawler"
SPIDER_MODULES = ["scraping_service.spiders"]


# logging settings
def setup_logging():
    if hasattr(setup_logging, "has_been_called"): return

    logging.basicConfig(
        handlers=[
            create_console_handler(level=logging.INFO),
            create_file_handler(level=logging.DEBUG, file_name=f'log_{date.today().isoformat()}.log', dir_name=LOG_DIR, file_mode='w')
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
