# Scrapy settings for CourtUsCrawler project
# For simplicity, this file contains only settings considered important or commonly used. Documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html
import os

# folders
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))    # root project dir
LOG_DIR = os.path.join(PROJECT_DIR, '_etc', 'logs')

INPUT_CSV_PATH = os.path.join(PROJECT_DIR, 'input.csv')
RESULTS_DIR = os.path.join(PROJECT_DIR, 'results')


# ENABLING CACHE SPEEDS UP THE FIRST CRAWLING (UNTIL CAPTCHA FACED), BUT MAY LEAD TO UNSOLVABLE CAPTCHAS
USE_CACHE = True
CACHE_JSON_PATH = os.path.join(PROJECT_DIR, '_etc', 'session_cache.json')


# crawling settings
DAYS_BACK = 10

TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
TWO_CAPTCHA_SITE_KEY = '6LdiezYUAAAAAGJqdPJPP7mAUgQUEJxyLJRUlvN6'
MAX_CAPTCHA_RETRIES = 10


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
        create_file_handler(level=logging.DEBUG, file_name='debug.log', dir_name=LOG_DIR, file_mode='w')
    ],
    format=DEFAULT_LOG_FORMAT,
    datefmt=DATE_FORMAT,
    level=logging.DEBUG     # not used, overriden in handlers
)


# # LogFormatter to handle DropItem silently
# LOG_FORMATTER = 'scrapy_app.settings.PoliteLogFormatter'
# 
# class PoliteLogFormatter(logformatter.LogFormatter):
#     def dropped(self, item, exception, response, spider):
#         return {
#             'level': logging.INFO,
#             'msg': "Dropped: %(exception)s",
#             'args': {'exception': exception, 'item': item}
#         }


# # export to CSV
# FEEDS = {
#   'results/items.csv': {
#        'format': 'csv'
#    }
#}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
