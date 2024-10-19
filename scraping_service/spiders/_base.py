from abc import ABC, abstractmethod
from scrapy import Spider, Request
from datetime import date, timedelta
from tqdm import tqdm
from django.db.models import Q
from typing import Literal

from utils.scrapy.decorators import update_progress
from apps.web.models import State, Company, Case, Document
from scraping_service.items import DocumentBodyItem
from scraping_service.settings import DAYS_BACK


class BaseSpider(ABC, Spider):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.state = State.objects.get(code=self.state_code)

        # min date to download documents and to rescrape existing cases
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)


class BaseCaseSearchSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.CaseSearchDbPipeline": 500
        })

    @property
    @abstractmethod
    def case_detail_relation(self) -> str:
        """Name of 1-to-1 relation from apps.web.models for CaseDetail state models. i.e., ny_details"""
        raise NotImplementedError

    def __init__(self, company_ids: list[int] = None):
        super().__init__()
        # get companies
        companies_to_scrape = Company.objects.all().prefetch_related('name_variations')

        # allow scrape specific companies (for debug purpose)
        if company_ids:
            companies_to_scrape = companies_to_scrape.filter(id__in=company_ids)

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
        self.existing_docket_ids: set[int] = set(
            Case.objects.filter(state=self.state).values_list('docket_id', flat=True)
        )
        self.logger.info(f"Found {len(self.existing_docket_ids)} existing case ids")


class BaseCaseDetailSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.CaseDetailDbPipeline": 500
        })

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

    def __init__(self, company_ids: list[int] = None, mode: Literal['new', 'existing', 'not_assigned'] = 'new'):
        super().__init__()
        self.cases_to_scrape = Case.objects.filter(
            state=self.state,
        ).select_related(
            self.case_detail_relation
        )

        # by default, scrape only records with is_scraped = False
        if mode == 'new':
            self.cases_to_scrape = self.cases_to_scrape.filter(
                is_scraped=False
            )
        elif mode == 'existing':
            self.cases_to_scrape = self.cases_to_scrape.filter(
                Q(case_date__gte=self.MIN_DATE) | Q(case_date__isnull=True)
            )
        elif mode == 'not_assigned':
            self.cases_to_scrape = self.cases_to_scrape.filter(
                case_number__icontains='not assigned',
                case_date__gte=self.MIN_DATE
            )

        # allow scrape specific companies (for debug purpose)
        if company_ids:
            self.cases_to_scrape = self.cases_to_scrape.filter(company_id__in=company_ids)

        self.logger.info(f"Found {self.cases_to_scrape.count()} cases to scrape")
        self.progress_bar = tqdm(total=self.cases_to_scrape.count())

        # get existing document ids
        self.existing_document_ids: set[int] = set(  # todo: use prefetch_related
            Document.objects.filter(case__state=self.state).values_list('unique_id', flat=True)
        )
        self.logger.info(f"Found {len(self.existing_document_ids)} existing document ids")


# there are documents with different links redirecting to the same page
class BaseDocumentDownloadSpider(BaseSpider, ABC):
    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("ITEM_PIPELINES", value={
            "scraping_service.pipelines.DocumentS3UploadPipeline": 300,
            "scraping_service.pipelines.DocumentDbPipeline": 500
        })

    def __init__(self):
        super().__init__()

        # min case date to crawl
        self.documents_to_scrape = Document.objects.filter(
            case__case_date__gte=self.MIN_DATE,
            case__state=self.state,
            is_downloaded=False
        ).select_related(
            'case'
        )
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
        yield DocumentBodyItem(record=document, body=response.body)
