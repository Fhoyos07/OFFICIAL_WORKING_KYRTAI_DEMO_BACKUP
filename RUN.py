from scrapy_app.utils.scrapy.crawler import crawl_sequential
from scrapy_app.spiders.spider import KyrNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider


def run():
    crawl_sequential(
        KyrNySearchSpider,
        KyrtNyCaseSpider,
        KyrtNyDocumentSpider
    )


if __name__ == '__main__':
    run()
