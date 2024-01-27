from scrapy.crawler import Spider, CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer

from typing import Type


def crawl(spider: Type[Spider], **kwargs):
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    process.crawl(spider, **kwargs)
    process.start()


def crawl_parallel(*spiders: Type[Spider]):
    """https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process"""
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    for spider in spiders:
        process.crawl(spider)
    process.start()


def crawl_sequential(*spiders: Type[Spider]):
    """https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process"""
    runner: CrawlerRunner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl_inner():
        for spider in spiders:
            yield runner.crawl(spider)
        reactor.stop()

    crawl_inner()
    reactor.run()
