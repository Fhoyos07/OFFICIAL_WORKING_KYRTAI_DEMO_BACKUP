from abc import ABC, abstractmethod
from scrapy import Spider, Request
from datetime import date, timedelta
from tqdm import tqdm
from pathlib import Path
from typing import Iterable
import sys

from utils.file import load_csv
from apps.web.models import State, Company, Case, Document
from scraping_service.settings import (DAYS_BACK, MAX_COMPANIES)


class BaseSpider(ABC, Spider):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.state = State.objects.get(code=self.state_code)


class BaseCaseSearchSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.CaseDbPipeline": 500
        })
        settings.set("CONCURRENT_REQUESTS",  value=1)

    @property
    @abstractmethod
    def case_detail_relation(self) -> str:
        """
        Name of 1-to-1 relation from apps.web.models for CaseDetail state models
        i.e., ny_details or ct_details
        """
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

        # min case date to crawl
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)


class BaseCaseDetailSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.CaseDbPipeline": 500
        })
        settings.set("CONCURRENT_REQUESTS", value=1)

    @property
    @abstractmethod
    def case_detail_relation(self) -> str:
        """
        Name of 1-to-1 relation from apps.web.models for CaseDetail state models
        i.e., ny_details or ct_details
        """
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.cases_to_scrape = Case.objects.filter(
            is_scraped=False
        ).select_related(
            self.case_detail_relation
        )
        self.logger.info(f"Found {self.cases_to_scrape.count()} cases to scrape")


class BaseDocumentDownloadSpider(ABC, Spider):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.documents_to_scrape = Document.objects.all()
        self.progress_bar = tqdm(total=len(self.documents_to_scrape.count()), file=sys.stdout, leave=False)

    def start_requests(self):
        for document in self.documents_to_scrape:
            yield Request(document.url,
                          callback=self.parse_document,
                          cb_kwargs=dict(document=document),
                          dont_filter=True)  # there are documents with different links redirecting to the same page

    def parse_document(self, response, document: Document):
        self.progress_bar.update()
        yield dict(
            body=response.body
        )
