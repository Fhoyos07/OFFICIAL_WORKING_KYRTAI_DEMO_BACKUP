from utils.scrapy.crawler import crawl_sequential
from utils.django import django_setup_decorator


@django_setup_decorator(environment='dev')
def run():
    from scraping_service.spiders.spider_ny import NyCaseSearchSpider, NyCaseDetailSpider, NyDocumentSpider
    crawl_sequential(
        NyCaseSearchSpider,
        NyCaseDetailSpider,
        NyDocumentSpider
    )


if __name__ == '__main__':
    run()
