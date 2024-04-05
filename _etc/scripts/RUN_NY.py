from utils.scrapy.crawler import crawl_sequential, crawl, crawl_with_crochet
from utils.django import django_setup_decorator


@django_setup_decorator(environment='dev')
def run():
    from scraping_service.spiders.spider_ny import NyCaseSearchSpider, NyCaseDetailSpider, NyDocumentSpider
    # crawl_with_crochet(NyCaseSearchSpider, company_ids=[907])
    crawl_with_crochet(NyCaseDetailSpider, mode='not_assigned')
    crawl_with_crochet(NyDocumentSpider)


if __name__ == '__main__':
    run()
