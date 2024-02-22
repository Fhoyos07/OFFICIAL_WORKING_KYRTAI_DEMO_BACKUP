from scraping_service.utils.scrapy.crawler import crawl_sequential
from scraping_service.spiders.spider_ny_proceedings import KyrtNyProceedingSearchSpider, KyrtNyProceedingCaseSpider, KyrtNyDocumentProceedingSpider


def run():
    crawl_sequential(
        KyrtNyProceedingSearchSpider,
        KyrtNyProceedingCaseSpider,
        KyrtNyDocumentProceedingSpider
    )


if __name__ == '__main__':
    run()
