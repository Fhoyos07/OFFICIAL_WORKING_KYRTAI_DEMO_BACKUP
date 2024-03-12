from scrapy.http import Request, FormRequest, TextResponse
import re

from utils.scrapy.response import extract_text_from_el
from utils.scrapy.decorators import log_response
from utils.scrapy.url import parse_url_params
from datetime import datetime
from django.utils import timezone

from utils.scrapy.decorators import update_progress

from ._base import BaseCaseDetailSpider, BaseCaseSearchSpider, BaseDocumentDownloadSpider
from apps.web.models import Company, Case, CaseDetailsCT, Document, DocumentDetailsCT
from scraping_service.items import DbItem


# Step 1 - search companies for new cases
class CtCaseSearchSpider(BaseCaseSearchSpider):
    name = 'ct_case_search'

    @property
    def state_code(self) -> str: return 'CT'

    @property
    def case_detail_relation(self): return 'ct_details'

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("CONCURRENT_REQUESTS",  value=10, priority='spider')

    def __init__(self):
        super().__init__()
        self.search_mode = 'Starts With'  # or 'Contains'

    def start_requests(self):
        yield Request('https://civilinquiry.jud.ct.gov/PartySearch.aspx',
                      callback=self.parse_search_form)

    @log_response
    def parse_search_form(self, response: TextResponse):
        i = 0
        for company, name_variations in self.queries_by_company.items():
            for name_variation in name_variations:
                i += 1
                yield FormRequest.from_response(
                    response=response,
                    formxpath='//form[@name="aspnetForm"]',
                    formdata={
                        'ctl00$ContentPlaceHolder1$txtLastName': name_variation,
                        'ctl00$ContentPlaceHolder1$ddlLastNameSearchType': self.search_mode
                    },
                    callback=self.parse_cases,
                    cb_kwargs=dict(company=company, name_variation=name_variation),
                    dont_filter=True,
                    priority=i
                )

    # @log_response
    def parse_cases(self, response: TextResponse, company: Company, name_variation: str, page: int = 1):
        # if page == 1:
        #     count_of_records = response.xpath('//*[@id="ctl00_ContentPlaceHolder1_lblRecords"]/text()').get()
        #     company_item = {
        #         "_type": 'Companies',
        #         "Company": company,
        #         "Cases Total": count_of_records.split(' of ')[-1] if count_of_records else 0
        #     }
        #     yield company_item
        result_rows = response.css('table.grdBorder .grdRow, table.grdBorder .grdRowAlt')
        self.logger.info(f'{name_variation} ({company.id}): Found {len(result_rows)} cases')

        for tr in result_rows:
            case_url = tr.xpath('td[3]/a/@href').get()
            if not case_url:
                self.logger.info(f'{name_variation} ({company.id}): Skipping as no case_url')
                continue

            # id is a built-in function, but we can explicitly ignore it for simplicity
            docket_id = parse_url_params(case_url)['DocketNo']

            # avoid scraping same case twice
            if docket_id in self.existing_docket_ids:
                self.logger.debug(f'{name_variation} ({company.id}): Skipping existing case {docket_id}')
                continue
            self.existing_docket_ids.add(docket_id)

            case = Case()
            case.ct_details = CaseDetailsCT()

            case.state = self.state
            case.company = company
            case.company_name_variation = name_variation

            case.docket_id = docket_id
            case.case_number = extract_text_from_el(tr.xpath('td[3]'))
            case.case_type = None  # populated in the next spider
            case.court = extract_text_from_el(tr.xpath('td[4]'))
            case.url = response.urljoin(case_url)

            case.caption = extract_text_from_el(tr.xpath('td[2]'))
            case.ct_details.party_name = extract_text_from_el(tr.xpath('td[1]'))
            case.ct_details.pty_number = extract_text_from_el(tr.xpath('td[5]'))
            case.ct_details.self_rep = extract_text_from_el(tr.xpath('td[6]')).lower() == 'y'
            yield DbItem(record=case)

        pagination_table = response.css('.grdBorder tr:nth-child(1) table tr')
        next_page_url = pagination_table.xpath('td[span]/following-sibling::td[1]/a/@href').get()
        if next_page_url:
            action, param = re.findall(r"__doPostBack\('(.+)','(.+)'\)", next_page_url)[0]
            yield FormRequest.from_response(
                response=response,
                formxpath='//form[@name="aspnetForm"]',
                formdata={'__EVENTTARGET': action, '__EVENTARGUMENT': param},
                callback=self.parse_cases,
                cb_kwargs=dict(company=company, name_variation=name_variation, page=page + 1),
                dont_filter=True
            )
        else:
            self.progress_bar.update()


# Step2 - Open each case and save document urls
class CtCaseDetailSpider(BaseCaseDetailSpider):
    name = 'ct_case_detail'

    @property
    def state_code(self): return 'CT'

    @property
    def case_detail_relation(self): return 'ct_details'

    @property
    def document_detail_relation(self): return 'ct_details'

    def start_requests(self):
        for case in self.cases_to_scrape:
            yield Request(case.url, callback=self.parse_case, cb_kwargs=dict(case=case))

    @update_progress
    def parse_case(self, response, case: Case):
        case.case_type = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblCaseType')
        case.ct_details.prefix = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblPrefixSuffix')

        file_date_str = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblFileDate')
        case.filed_date = datetime.strptime(file_date_str, "%m/%d/%Y").date()

        return_date_str = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblReturnDate')
        case.ct_details.return_date = datetime.strptime(return_date_str, "%m/%d/%Y").date()

        case.is_scraped = True
        case.scraped_date = timezone.now()
        yield DbItem(record=case)

        if case.filed_date < self.MIN_DATE: return  # don't save cases for all records

        document_rows = response.xpath(
            '//*[@id="ctl00_ContentPlaceHolder1_CaseDetailDocuments1_pnlMotionData"]'
            '//table'
            '//table'
            '//tr[position()>1]'
        )
        for tr in document_rows:
            document_url = tr.xpath('td[4]/a/@href').get()
            if not document_url:
                self.logger.debug(f'Invalid document_url: {document_url} at {response.url}')
                continue

            document = Document(case=case)
            document.ct_details = DocumentDetailsCT()

            # common fields
            document.url = response.urljoin(document_url)
            document.name = tr.xpath('td[4]/a/text()').get()
            document.document_id = parse_url_params(document_url)['DocumentNo']

            # CT-specific fields
            document.ct_details.entry_no = extract_text_from_el(tr.xpath('td[1]'))

            file_date = extract_text_from_el(tr.xpath('td[2]'))
            document.ct_details.filed_date = datetime.strptime(file_date, "%m/%d/%Y").date()

            document.ct_details.filed_by = extract_text_from_el(tr.xpath('td[3]'))
            document.ct_details.arguable = extract_text_from_el(tr.xpath('td[5]'))
            yield DbItem(record=document)

    @staticmethod
    def extract_header(response, attr_id: str) -> str | None:
        value = response.xpath(f'//*[@id="{attr_id}"]/text()').get()
        if value:
            return value.strip()


# Step 3 - open and download each document
class CtDocumentSpider(BaseDocumentDownloadSpider):
    name = 'kyrt_ct_documents'
    @property
    def state_code(self) -> str: return 'CT'

    custom_settings = dict(
        CONCURRENT_REQUESTS=10,
        ITEM_PIPELINES={"scraping_service.pipelines.DocumentSavePipeline": 300}  # download PDFs
    )
