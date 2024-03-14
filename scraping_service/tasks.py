from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from celery import shared_task, chain, signals
from datetime import datetime
import crochet
import logging

from utils.scrapy.crawler import crawl_with_crochet


@signals.worker_process_init.connect
def configure_infrastructure(**kwargs):
    """Fix for Twisted.ReactorNotRestartable issue with Scrapy"""
    crochet.setup()


@shared_task
def run_spider(spider_name: str, *args, **kwargs) -> bool:
    crawl_with_crochet(spider_name, *args, **kwargs)
    return True


@shared_task
def run_example_chain() -> bool:
    # chain(
    #     run_spider.si('prototype'),
    #     run_spider.si('prototype')
    # )()
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
