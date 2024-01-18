from scrapy.spiders import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from typing import Type


def crawl(spider: Type[Spider], **kwargs):
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    process.crawl(spider, **kwargs)
    process.start()


def crawl_many(*spiders: Type[Spider]):
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    for spider in spiders:
        process.crawl(spider)
    process.start()
