from abc import ABC, abstractmethod
from scrapy import Spider, Request
from datetime import date, timedelta
from tqdm import tqdm
from pathlib import Path
from typing import Iterable
from django.db import models
import sys

from apps.web.models import State, Company, Case, Document

from utils.scrapy.decorators import update_progress

from scraping_service.items import DocumentBodyItem
from scraping_service.settings import (DAYS_BACK, MAX_COMPANIES)


class BaseSpider(ABC, Spider):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.state = State.objects.get(code=self.state_code)

        # min case date to crawl
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)


class BaseCaseSearchSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.CaseSearchDbPipeline": 500
        })
        settings.set("CONCURRENT_REQUESTS",  value=1)

    @property
    @abstractmethod
    def case_detail_relation(self) -> str:
        """Name of 1-to-1 relation from apps.web.models for CaseDetail state models. i.e., ny_details"""
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        # get companies
        companies_to_scrape = Company.objects.all().prefetch_related('name_variations')
        if MAX_COMPANIES:
            companies_to_scrape = companies_to_scrape[:MAX_COMPANIES]
        self.logger.info(f"Found {companies_to_scrape.count()} companies to scrape")

        # add queries to companies
        self.queries_by_company: dict[Company, list] = {}
        for company in companies_to_scrape:
            name_variations_set = {company.name} | set(n.name for n in company.name_variations.all())
            self.queries_by_company[company] = sorted(list(name_variations_set), key=len, reverse=True)

        # sort by name
        self.queries_by_company = dict(sorted(self.queries_by_company.items(), key=lambda x: x[0].name))

        # set up progress bar
        total = sum(len(queries) for queries in self.queries_by_company.values())
        self.logger.info(f"Total {total} queries")
        self.progress_bar = tqdm(total=total)

        # get existing case ids
        self.existing_docket_ids = set(Case.objects.filter(state=self.state).values_list('docket_id', flat=True))
        self.logger.info(f"Found {len(self.existing_docket_ids)} existing case ids")


class BaseCaseDetailSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.CaseDetailDbPipeline": 500
        })
        settings.set("CONCURRENT_REQUESTS", value=1)

    @property
    @abstractmethod
    def case_detail_relation(self) -> str:
        """Name of 1-to-1 relation from apps.web.models for CaseDetail state models. i.e., ny_details"""
        raise NotImplementedError

    @property
    @abstractmethod
    def document_detail_relation(self) -> str:
        """Name of 1-to-1 relation from apps.web.models for DocumentDetail state models. i.e., ny_details"""
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.cases_to_scrape = Case.objects.filter(
            is_scraped=False, state=self.state
        ).select_related(
            self.case_detail_relation
        )
        self.logger.info(f"Found {self.cases_to_scrape.count()} cases to scrape")
        self.progress_bar = tqdm(total=self.cases_to_scrape.count())


# there are documents with different links redirecting to the same page
class BaseDocumentDownloadSpider(BaseSpider, ABC):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.documents_to_scrape = Document.objects.filter(case__state=self.state)
        self.progress_bar = tqdm(total=self.documents_to_scrape.count())

    def start_requests(self):
        for document in self.documents_to_scrape:
            yield Request(
                document.url,
                callback=self.parse_document,
                cb_kwargs=dict(document=document),
                dont_filter=True  # there are documents with different links redirecting to the same page
            )

    @update_progress
    def parse_document(self, response, document: Document):
        self.progress_bar.update()
        yield DocumentBodyItem(document_id=document.id, body=response.body)
