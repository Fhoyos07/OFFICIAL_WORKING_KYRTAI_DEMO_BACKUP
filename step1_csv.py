from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os

from scrapy_app.spiders.spider import KyrtNyCaseSpider


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))   # set working dir to current
    process = CrawlerProcess(get_project_settings())
    process.crawl(KyrtNyCaseSpider)
    process.start()                       # script will block here until crawling finish
