from utils.scrapy.crawler import crawl_sequential
from scraping_service.spiders.spider_ny import KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider


def run():
    crawl_sequential(
        KyrtNySearchSpider,
        KyrtNyCaseSpider,
        KyrtNyDocumentSpider
    )


if __name__ == '__main__':
    run()
