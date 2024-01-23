from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from scrapy_app.spiders.spider import CourtsNySpider, CourtsNyFileSpider


def run():
    # https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process
    runner: CrawlerRunner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(CourtsNySpider)
        yield runner.crawl(CourtsNyFileSpider)
        reactor.stop()

    crawl()
    reactor.run()


if __name__ == '__main__':
    run()
