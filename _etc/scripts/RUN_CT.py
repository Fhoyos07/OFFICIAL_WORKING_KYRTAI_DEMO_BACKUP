from pathlib import Path
import sys
PROJECT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_DIR))


from utils.scrapy.crawler import crawl_sequential
from utils.django import django_setup_decorator


@django_setup_decorator()
def run():
    from scraping_service.spiders.spider_ct import CtCaseSearchSpider, CtCaseDetailSpider, KyrtCtDocumentSpider
    from apps.web.models import Case, Document
    # Document.objects.filter(case__state__code='CT').delete()
    # Case.objects.filter(state__code='CT').delete()

    crawl_sequential(
        CtCaseSearchSpider,
        CtCaseDetailSpider,
        # KyrtCtDocumentSpider
    )


if __name__ == '__main__':
    run()
