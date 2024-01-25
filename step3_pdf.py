from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os

from scrapy_app.spiders.spider import KyrtNyDocumentSpider


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))   # set working dir to current
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    process.crawl(KyrtNyDocumentSpider)
    process.start()                       # script will block here until crawling finish
