from utils.scrapy.crawler import crawl_sequential, crawl, crawl_with_crochet
from utils.django import django_setup_decorator


@django_setup_decorator()
def run():
    from scraping_service.spiders.spider_ct import CtCaseSearchSpider, CtCaseDetailSpider, CtDocumentSpider
    from apps.web.models import Case, Document
    # Document.objects.filter(case__state__code='CT').delete()
    # Case.objects.filter(state__code='CT').delete()

    # crawl_with_crochet(CtCaseSearchSpider, company_ids=[907])
    crawl_with_crochet(CtCaseDetailSpider, company_ids=[907], mode='new')
    # crawl_with_crochet(CtDocumentSpider)


if __name__ == '__main__':
    run()
