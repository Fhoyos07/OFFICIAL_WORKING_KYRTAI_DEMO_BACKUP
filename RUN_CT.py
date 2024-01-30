from scrapy_app.utils.scrapy.crawler import crawl_sequential
from scrapy_app.spiders.spider_ct import KyrtCtSearchSpider, KyrtCtDocumentSpider


def run():
    crawl_sequential(
        KyrtCtSearchSpider,
        KyrtCtDocumentSpider
    )


if __name__ == '__main__':
    run()
