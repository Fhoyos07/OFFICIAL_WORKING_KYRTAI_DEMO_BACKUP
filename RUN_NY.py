from scrapy_app.utils.scrapy.crawler import crawl_sequential
from scrapy_app.spiders.spider_ny import KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider


def run():
    crawl_sequential(
        KyrtNySearchSpider,
        KyrtNyCaseSpider,
        KyrtNyDocumentSpider
    )


if __name__ == '__main__':
    run()
