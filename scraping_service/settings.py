# Scrapy settings for CourtUsCrawler project
# For simplicity, this file contains only settings considered important or commonly used. Documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html
import os
from django.conf import settings


# folders
BASE_DIR = settings.BASE_DIR
ETC_DIR = BASE_DIR / '_etc'
HTML_DEBUG_DIR = ETC_DIR / 'html'
FILES_DIR = BASE_DIR / 'files'       # root dir for csvs, input and pdfs
INPUT_CSV_PATH = FILES_DIR / 'input.csv'


# only 1 concurrent request an no pipelines by default (override on spider level if needed)
CONCURRENT_REQUESTS = 1
ITEM_PIPELINES = {}


# crawling settings
DAYS_BACK = 14


# captcha settings
TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
MAX_CAPTCHA_RETRIES = 20


# Amazon S3 settings
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_S3_BUCKET_NAME = settings.AWS_S3_BUCKET_NAME


# Proxymesh Settings
PROXYMESH_ENABLED = False
PROXYMESH_USER = 'madfatcat'
PROXYMESH_PASSWORD = 'password'
PROXYMESH_ENDPOINT = 'nl.proxymesh.com'


# NY credentials
NY_USERNAME = 'unihunko'
NY_PASSWORD = 'tugce0-dykzyz-fuvxoM'


# Smartproxy Settings
SMARTPROXY_ENABLED = False
SMARTPROXY_USER = os.environ.get('SMARTPROXY_USER')
SMARTPROXY_PASSWORD = os.environ.get('SMARTPROXY_PASSWORD')
SMARTPROXY_ENDPOINT = 'us.smartproxy.com'
SMARTPROXY_PORT = '10000'

DOWNLOADER_MIDDLEWARES = {
    'scraping_service.proxies.proxymesh.ProxyMeshMiddleware': 110,    # set PROXYMESH_ENABLED to True to activate
    'scraping_service.proxies.smartproxy.SmartProxyMiddleware': 110,  # set SMARTPROXY_ENABLED to True to activate
}


# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


# standard settings
BOT_NAME = "CourtUsCrawler"
SPIDER_MODULES = ["scraping_service.spiders"]


# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
