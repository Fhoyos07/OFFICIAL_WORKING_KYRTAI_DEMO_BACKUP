from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from scrapy_app.spiders.spider import KyrNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider


def run():
    # https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process
    runner: CrawlerRunner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(KyrNySearchSpider)
        yield runner.crawl(KyrtNyCaseSpider)
        yield runner.crawl(KyrtNyDocumentSpider)
        reactor.stop()

    crawl()
    reactor.run()


if __name__ == '__main__':
    run()
