from utils.scrapy.crawler import crawl_sequential
from scraping_service.spiders.spider_ny import NyCaseSearchSpider, NyCaseDetailSpider, NyDocumentSpider


def run():
    crawl_sequential(
        NyCaseSearchSpider,
        NyCaseDetailSpider,
        NyDocumentSpider
    )


if __name__ == '__main__':
    run()
