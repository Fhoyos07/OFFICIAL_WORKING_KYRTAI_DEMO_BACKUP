from utils.scrapy.crawler import crawl_sequential
from utils.django import django_setup_decorator


@django_setup_decorator()
def run():
    from scraping_service.spiders.spider_ct import CtCaseSearchSpider, CtCaseDetailSpider, KyrtCtDocumentSpider
    crawl_sequential(
        CtCaseSearchSpider,
        # KyrtCtDocumentSpider
    )


if __name__ == '__main__':
    run()
