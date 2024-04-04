from scrapy import Request, FormRequest
from scrapy.exceptions import CloseSpider
from datetime import datetime

from apps.web.models import Company, Case, CaseDetailsNY, Document, DocumentDetailsNY
from utils.scrapy.decorators import log_response, save_response, update_progress
from utils.types.str import trim_spaces
from utils.scrapy.url import parse_url_params
from typing import Iterable

from ._base import BaseCaseSearchSpider, BaseCaseDetailSpider, BaseDocumentDownloadSpider
from scraping_service.items import DbItem
from scraping_service.settings import NY_USERNAME, NY_PASSWORD


class NyCaseSearchSpider(BaseCaseSearchSpider):
    """Step 1 - search companies for new cases"""
    name = 'ny_case_search'

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        # settings.set("DOWNLOAD_DELAY",  value=0.5, priority='spider')

    @property
    def state_code(self) -> str: return 'NY'

    @property
    def case_detail_relation(self): return 'ny_details'

    def __init__(self):
        super().__init__()
        # flatten input list of company and variations to allow pop
        self.queries: list[tuple[str, Company]] = []
        for company, name_variations in self.queries_by_company.items():
            for name_variation in name_variations:
                self.queries.append((name_variation, company))

        self.current_company, self.current_name_variation = None, None

    def start_requests(self):
        yield Request('https://iapps.courts.state.ny.us/nyscef/Login', callback=self.parse_login)

    @log_response
    def parse_login(self, response):
        login_data = dict(
            txtUserName=NY_USERNAME,
            pwPassword=NY_PASSWORD
        )
        yield FormRequest.from_response(response,
                                        formname='form',
                                        formdata=login_data,
                                        callback=self.parse_after_login)

    @log_response
    def parse_after_login(self, response):
        yield self.start_company_request()

    def start_company_request(self):
        if not self.queries: return

        self.current_name_variation, self.current_company = self.queries.pop(0)
        self.logger.info(f"Started search for company {self.current_company}, variation {self.current_name_variation}")
        url = 'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name'
        return Request(url, callback=self.parse_search_form, dont_filter=True)

    @log_response
    def parse_search_form(self, response):
        self._validate_response(response)

        search_data = dict(txtBusinessOrgName=self.current_name_variation)
        yield FormRequest.from_response(response,
                                        formname='form',
                                        formdata=search_data,
                                        callback=self.parse_cases,
                                        dont_filter=True)

    @log_response
    def parse_cases(self, response):
        self._validate_response(response)

        sort_data = dict(selSortBy='FilingDateDesc')
        yield FormRequest.from_response(response,
                                        formname='form',
                                        formdata=sort_data,
                                        callback=self.parse_sorted_cases,
                                        dont_filter=True)

    @log_response
    def parse_sorted_cases(self, response):
        self._validate_response(response)
        name_variation, company = self.current_name_variation, self.current_company

        result_rows = response.css('.NewSearchResults tbody tr')
        search_title = response.css('.Document_Row strong::text').get()
        self.logger.debug(f'Name variation: {name_variation}, page_title: {search_title}')
        self.logger.info(f'{name_variation} ({company.id}): Found {len(result_rows)} cases')

        # flag to detect if scraping next page is required
        new_cases_found = False

        for tr in result_rows:
            # find case_url
            case_url = tr.xpath('td[1]/a/@href').get()
            if not case_url:
                self.logger.error(f'Invalid case_url {case_url} at {response.url}')
                continue

            # avoid scraping same case twice
            docket_id = parse_url_params(case_url)['docketId']
            if docket_id in self.existing_docket_ids:
                self.logger.info(f'Case #{docket_id} exists. Skipping.')
                continue
            self.existing_docket_ids.add(docket_id)

            # parse case number and date
            first_cell_texts: list[str] = tr.xpath('td[1]//text()[normalize-space()]').getall()
            case_number, received_date_str = [s.strip() for s in first_cell_texts]

            # set flag to true to make scraping next page
            new_cases_found = True

            case = Case(
                state=self.state,
                company=company,
                company_name_variation=name_variation,
            )
            case.ny_details = CaseDetailsNY()

            case.docket_id = docket_id
            case.case_number = case_number
            case.case_type = tr.xpath('td[4]/span/text()').get()
            case.court = tr.xpath('td[4]/text()').get(default='').strip()
            case.caption = tr.xpath('td[3]/text()').get()
            case.url = response.urljoin(case_url)

            case.case_date = case.received_date = datetime.strptime(received_date_str, '%m/%d/%Y').date()

            case.status = tr.xpath('td[2]/span/text()').get()

            case.ny_details.efiling_status = tr.xpath('td[2]/text()').get(default='').strip()
            yield DbItem(record=case)

        next_page_url = response.xpath('//span[contains(@class,"pageNumbers")]/a[text()=">>"]/@href').get()
        if new_cases_found and next_page_url:
            yield response.follow(next_page_url,
                                  callback=self.parse_sorted_cases,
                                  dont_filter=True)
        else:
            # finished scraping company
            self.progress_bar.update()
            yield self.start_company_request()

    def _validate_response(self, response):
        # todo: check also for My Cases in the left menu
        if response.xpath('//form[@name="captcha_form"]'):
            self.logger.error('Captcha found! Existing')
            raise CloseSpider('Captcha found')


class NyCaseDetailSpider(BaseCaseDetailSpider):
    """Step2 - Open each case and save document urls"""
    name = 'ny_case_detail'

    @property
    def state_code(self) -> str: return 'NY'

    @property
    def case_detail_relation(self): return 'ny_details'

    @property
    def document_detail_relation(self): return 'ny_details'

    def start_requests(self) -> Iterable[Request]:
        for case in self.cases_to_scrape:
            # crawl case page to parse documents
            yield Request(case.url, callback=self.parse_case, cb_kwargs=dict(case=case), dont_filter=True)

    @update_progress
    def parse_case(self, response, case: Case):
        # update case (scraped_date and is_scraped are updated in pipeline)
        yield DbItem(record=case)

        document_rows = response.css('table.NewSearchResults tbody tr')
        for tr in document_rows:
            document_url = tr.xpath('td[2]/a/@href').get()
            if not document_url:
                self.logger.debug(f'Invalid document_url: {document_url} at {response.url}')
                continue

            # avoid scraping same document twice
            document_id = parse_url_params(document_url)['docIndex']
            if document_id in self.existing_document_ids:
                self.logger.debug(f'Case #{case.docket_id}: Skipping existing document {document_id}')
                continue

            document = Document(case=case)
            document.ny_details = DocumentDetailsNY()

            document.document_id = document_id
            document.url = response.urljoin(document_url)

            name_parts = tr.xpath('td[2]/a/text()[normalize-space()] | td[2]/text()[normalize-space()]').getall()
            document.name = ' '.join(trim_spaces(p) for p in name_parts)

            # NY-specific fields
            description_parts = tr.xpath('td[2]/span/text()[normalize-space()]').getall()
            if description_parts:
                document.ny_details.description = ' '.join(trim_spaces(p) for p in description_parts)

            filed_parts = [trim_spaces(s) for s in tr.xpath('td[3]//text()[normalize-space()]').getall()]
            if any('Filed:' in p for p in filed_parts):
                document.ny_details.filed_by = filed_parts[0]
                for p in filed_parts[1:]:
                    if p.startswith('Filed:'):
                        filed_date_str = p.replace('Filed: ', '')
                        document.ny_details.filed_date = datetime.strptime(filed_date_str, '%m/%d/%Y').date()
                    if p.startswith('Received:'):
                        received_date_str = p.replace('Received: ', '')
                        document.ny_details.filed_date = datetime.strptime(received_date_str, '%m/%d/%Y').date()

            status_document_url = tr.xpath('td[4]/a/@href').get()
            if status_document_url:
                document.ny_details.status_document_url = response.urljoin(status_document_url)
                document.ny_details.status_document_name = tr.xpath('td[4]/a/text()').get()
            yield DbItem(record=document)


class NyDocumentSpider(BaseDocumentDownloadSpider):
    """Step 3 - download each document"""
    name = 'ny_documents'

    @property
    def state_code(self) -> str: return 'NY'
