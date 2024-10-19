from utils.scrapy.crawler import crawl_sequential
from scraping_service.spiders.spider_ny_proceedings import NyProceedingCaseSearchSpider, NyProceedingCaseDetailSpider, NyDocumentProceedingSpider


def run():
    crawl_sequential(
        NyProceedingCaseSearchSpider,
        NyProceedingCaseDetailSpider,
        NyDocumentProceedingSpider
    )


if __name__ == '__main__':
    run()
