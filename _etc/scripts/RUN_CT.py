from utils.scrapy.crawler import crawl_sequential
from utils.django import django_setup_decorator


@django_setup_decorator()
def run():
    from scraping_service.spiders.spider_ct import CtCaseSearchSpider, CtCaseDetailSpider, KyrtCtDocumentSpider
    from apps.web.models import Case
    ct_cases = Case.objects.filter(state__code='CT')
    print(f'Deleting {len(ct_cases)} cases')
    ct_cases.delete()
    crawl_sequential(
        CtCaseSearchSpider,
        # CtCaseDetailSpider,
        # KyrtCtDocumentSpider
    )


if __name__ == '__main__':
    run()
