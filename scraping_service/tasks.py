from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from celery import shared_task, chain, signals
from datetime import datetime
import crochet
import logging

from utils.scrapy.crawler import crawl_with_crochet

from scraping_service.spiders._base import BaseSpider
from scraping_service.spiders.spider_ct import CtCaseSearchSpider, CtCaseDetailSpider, CtDocumentSpider
from scraping_service.spiders.spider_ny import NyCaseSearchSpider, NyCaseDetailSpider, NyDocumentSpider


def get_spiders() -> dict[str, dict[str, type(BaseSpider)]]:
    return {
        "NY": {
            "case_search": NyCaseSearchSpider,
            "case_detail": NyCaseDetailSpider,
            "document": NyDocumentSpider,
        },
        "CT": {
            "case_search": CtCaseSearchSpider,
            "case_detail": CtCaseDetailSpider,
            "document": CtDocumentSpider,
        }
    }


@signals.worker_process_init.connect
def configure_infrastructure(**kwargs):
    """Fix for Twisted.ReactorNotRestartable issue with Scrapy"""
    crochet.setup()


# main tasks
@shared_task
def scrape_new_cases(state_code: str, *args, **kwargs) -> bool:
    state_spiders: dict[str, type(BaseSpider)] = get_spiders()[state_code]
    crawl_with_crochet(state_spiders['case_search'])
    crawl_with_crochet(state_spiders['case_detail'], mode='new')
    crawl_with_crochet(state_spiders['document'])
    return True


@shared_task
def scrape_existing_cases(state_code: str, *args, **kwargs) -> bool:
    state_spiders: dict[str, type(BaseSpider)] = get_spiders()[state_code]
    crawl_with_crochet(state_spiders['case_detail'], mode='existing')
    crawl_with_crochet(state_spiders['document'])
    return True


@shared_task
def scrape_not_assigned_cases(state_code: str, *args, **kwargs) -> bool:
    state_spiders: dict[str, type(BaseSpider)] = get_spiders()[state_code]
    crawl_with_crochet(state_spiders['case_detail'], mode='not_assigned')
    crawl_with_crochet(state_spiders['document'])
    return True


# debug tasks
@shared_task
def run_spider(spider_name: str, *args, **kwargs) -> bool:
    crawl_with_crochet(spider_name, *args, **kwargs)
    return True


@shared_task
def run_example_chain() -> bool:
    crawl_with_crochet(spider='prototype')
    crawl_with_crochet(spider='prototype')
    return True


@shared_task
def pulse() -> datetime:
    """A Celery task to run the spider based on exchange."""
    now = datetime.now()
    logging.info(f'Current time logging: {now}')
    print(f'Current time print: {now}')
    return now
