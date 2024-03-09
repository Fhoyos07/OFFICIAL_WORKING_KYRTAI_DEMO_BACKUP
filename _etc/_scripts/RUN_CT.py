from utils.scrapy.crawler import crawl_sequential
from scraping_service.spiders.spider_ct import KyrtCtSearchSpider, KyrtCtCaseSpider, KyrtCtDocumentSpider


def run():
    crawl_sequential(
        KyrtCtSearchSpider,
        # KyrtCtDocumentSpider
    )


if __name__ == '__main__':
    run()
