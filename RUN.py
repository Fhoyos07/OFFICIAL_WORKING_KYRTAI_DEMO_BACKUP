from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os


def crawl(spider_name: str):
    os.chdir(os.path.dirname(__file__))   # set working dir to current
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_name)
    process.start()                       # script will block here until crawling finish


if __name__ == "__main__":
    crawl(spider_name="prototype")
