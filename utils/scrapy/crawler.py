from scrapy.crawler import Spider, CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
import logging
import crochet


def crawl_with_crochet(spider: type[Spider] | str, *args, **kwargs):
    try:
        crochet.setup()   # avoids ReactorNotRestartable error

        @crochet.wait_for(timeout=60 * 60 * 5)  # Wait for spider completion for 5 hours before throwing TimeoutError
        def run_in_reactor():
            runner = CrawlerRunner(get_project_settings())
            return runner.crawl(spider, *args, **kwargs)  # return the Deferred that fires when the crawl is done

        # block until the Deferred returned by runner.crawl() fires
        run_in_reactor()
        logging.info(f'Spider {spider} finished')

    except Exception as e:
        logging.exception(e)
        raise


def crawl(spider: type[Spider], **kwargs):
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    process.crawl(spider, **kwargs)
    process.start()


def crawl_parallel(*spiders: type[Spider]):
    """https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process"""
    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    for spider in spiders:
        process.crawl(spider)
    process.start()


def crawl_sequential(*spiders: type[Spider]):
    """https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process"""
    runner: CrawlerRunner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl_inner():
        for spider in spiders:
            yield runner.crawl(spider)
        reactor.stop()

    crawl_inner()
    reactor.run()
