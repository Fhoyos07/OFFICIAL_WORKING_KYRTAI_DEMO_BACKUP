# Scrapy settings for CourtUsCrawler project
# For simplicity, this file contains only settings considered important or commonly used. Documentation:
#     https://docs.scrapy.org/en/latest/topics/settings.html
import os


# folders
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))    # root project dir
LOG_DIR = os.path.join(PROJECT_DIR, '_etc', 'logs')
CSV_DIR = os.path.join(PROJECT_DIR, '_etc', '_results')


# Configure item pipelines: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "scrapy_app.pipelines.CsvOnClosePipeline": 300,
}


# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# standard settings
BOT_NAME = "CourtUsCrawler"
SPIDER_MODULES = ["scrapy_app.spiders"]

# CONCURRENT_REQUESTS = 32                  # default: 32
# CONCURRENT_REQUESTS_PER_DOMAIN = 16       # default: 16
# DOWNLOAD_DELAY = 3                        # default: 0
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }
# ROBOTSTXT_OBEY = False                    # don't obey robots.txt rules


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
