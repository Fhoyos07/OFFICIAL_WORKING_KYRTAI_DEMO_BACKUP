from abc import ABC, abstractmethod
from scrapy import Spider, Request
from datetime import date, timedelta
from tqdm import tqdm
from pathlib import Path
from typing import Iterable
import sys

from ..utils.file import load_csv
from ..settings import (INPUT_CSV_PATH, FILES_DIR, DAYS_BACK, MAX_COMPANIES)


class BaseCaseSearchSpider(ABC, Spider):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    @property
    def input_csv_path(self) -> Path: return INPUT_CSV_PATH

    def __init__(self):
        super().__init__()

        # parse input CSV
        companies_to_scrape = []
        for row in load_csv(self.input_csv_path):
            company = row['Competitor / Fictitious LLC Name'].strip().upper().replace(', LLC', ' LLC')
            if company:
                companies_to_scrape.append(company)
        self.logger.info(f"Before deduplication: {len(companies_to_scrape)} companies")
        self.QUERIES = sorted(list(set(companies_to_scrape)))
        self.logger.info(f"After deduplication: {len(self.QUERIES)} companies")

        # if MAX_COMPANIES in settings - cut companies
        if MAX_COMPANIES:
            self.QUERIES = companies_to_scrape[:MAX_COMPANIES]
            self.logger.info(f"Cut companies to only {len(self.QUERIES)} first")

        # load existing cases ids
        cases_path: Path = FILES_DIR / self.state_code / f'cases.csv'
        self.existing_case_ids = {r['Case Id'] for r in load_csv(cases_path)} if cases_path.exists() else set()

        # delete companies file
        companies_path: Path = FILES_DIR / self.state_code / f'companies.csv'
        if companies_path.exists():
            companies_path.unlink()

        # min case date to crawl
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)

        # set up progress bar
        self.progress_bar = tqdm(total=len(self.QUERIES), file=sys.stdout, leave=False)


class BaseDocumentDownloadSpider(ABC, Spider):
    @property
    @abstractmethod
    def state_code(self) -> str: raise NotImplementedError

    def __init__(self):
        super().__init__()

        # parse input CSV
        self.document_name_by_url: dict[str, str] = {}

        documents_path: Path = FILES_DIR / self.state_code / f'documents.csv'
        documents = load_csv(documents_path) if documents_path.exists() else []
        for url, file_path in self._prepare_documents_to_scrape(csv_rows=documents):
            self.document_name_by_url[url] = file_path
        self.progress_bar = tqdm(total=len(self.document_name_by_url), file=sys.stdout, leave=False)

    def _prepare_documents_to_scrape(self, csv_rows: list[dict]) -> Iterable[tuple[str, str]]:
        for row in csv_rows:
            file_path = self._generate_file_path(row, fields=['Company', 'Case Number', 'Document ID'])
            yield row['Document URL'], file_path

    def start_requests(self):
        for url, relative_file_path in self.document_name_by_url.items():
            yield Request(url,
                          callback=self.parse_document,
                          cb_kwargs=dict(relative_file_path=relative_file_path),
                          dont_filter=True)  # there are documents with different links redirecting to the same page

    def parse_document(self, response, relative_file_path: str):
        self.progress_bar.update()
        yield dict(
            body=response.body,
            relative_file_path=relative_file_path
        )

    @staticmethod
    def _generate_file_path(row: dict, fields: list[str]):
        return '/'.join(row[k].replace('/', '_') for k in fields) + '.pdf'
