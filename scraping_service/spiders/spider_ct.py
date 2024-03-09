from scrapy import Spider
from scrapy.http import Request, FormRequest, TextResponse
import re

from utils.scrapy.response import extract_text_from_el
from utils.scrapy.decorators import log_response
from utils.scrapy.url import parse_url_params
from datetime import datetime

from ._base import BaseCaseSearchSpider, BaseDocumentDownloadSpider
from apps.web.models import Company, Case
from scraping_service.items import CaseItem, CaseItemCT, DocumentItem, DocumentItemCT


# Step 1 - search each company
class KyrtCtSearchSpider(BaseCaseSearchSpider):
    name = 'kyrt_ct_search'

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("CONCURRENT_REQUESTS", value=1)

    @property
    def state_code(self) -> str: return 'CT'

    def __init__(self):
        super().__init__()
        self.search_mode = 'Starts With'  # or 'Contains'

    def start_requests(self):
        yield Request('https://civilinquiry.jud.ct.gov/PartySearch.aspx',
                      callback=self.parse_search_form)

    @log_response
    def parse_search_form(self, response: TextResponse):
        for company, name_variations in self.queries_by_company.items():
            for name_variation in name_variations:
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
            case_id = parse_url_params(case_url)['DocketNo']

            # avoid scraping same case twice
            if case_id in self.existing_case_ids:
                self.logger.info(f'{name_variation} ({company.id}): Skipping existing case {case_id}')
                continue
            self.existing_case_ids.add(case_id)

            case_item = CaseItemCT()
            case_item.state = self.state
            case_item.company = company
            case_item.company_name_variation = name_variation

            case_item.case_id = case_id
            case_item.case_number = extract_text_from_el(tr.xpath('td[3]'))
            case_item.case_type = None  # populated in the next spider
            case_item.court = extract_text_from_el(tr.xpath('td[4]'))
            case_item.url = response.urljoin(case_url)

            case_item.caption = extract_text_from_el(tr.xpath('td[2]'))
            case_item.party_name = extract_text_from_el(tr.xpath('td[1]'))
            case_item.pty_number = extract_text_from_el(tr.xpath('td[5]'))
            case_item.self_rep = extract_text_from_el(tr.xpath('td[6]')).lower() == 'y'
            yield Request(url=case_item.url,
                          callback=self.parse_case,
                          cb_kwargs=dict(case_item=case_item))

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

    @log_response
    def parse_case(self, response, case_item: CaseItem):
        case_item.prefix = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblPrefixSuffix')
        case_item.case_type = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblCaseType')

        case_file_date_str = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblFileDate')
        file_date = datetime.strptime(case_file_date_str, "%m/%d/%Y").date()
        case_item.file_date = file_date.isoformat()

        return_date = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblReturnDate')
        case_item.return_date = datetime.strptime(return_date, "%m/%d/%Y").date()
        yield case_item

    @staticmethod
    def extract_header(response, attr_id: str) -> str | None:
        value = response.xpath(f'//*[@id="{attr_id}"]/text()').get()
        if value:
            return value.strip()


# Step2 - Open each case and save document urls
class KyrtCtCaseSpider(Spider):
    def start_requests(self):
        pass

    def parse_case(self, response, case: Case):
        # skip documents extraction for old cases
        if file_date < self.MIN_DATE:
            return

        # extract documents
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

            document_item = DocumentItemCT()
            document_item.state = self.state
            document_item.url = response.urljoin(document_url)
            document_item.company = case_item.company
            document_item.case = case_item.case_number
            document_item.name = tr.xpath('td[4]/a/text()').get()
            document_item.document_id = parse_url_params(document_url)['DocumentNo']
            document_item.entry_no = extract_text_from_el(tr.xpath('td[1]'))

            file_date = extract_text_from_el(tr.xpath('td[2]'))
            document_item.file_date = datetime.strptime(file_date, "%m/%d/%Y").date()

            document_item.filed_by = extract_text_from_el(tr.xpath('td[3]'))
            document_item.arguable = extract_text_from_el(tr.xpath('td[5]'))
            yield document_item


# Step 3 - open and download each document
class KyrtCtDocumentSpider(BaseDocumentDownloadSpider):
    name = 'kyrt_ct_documents'
    @property
    def state_code(self) -> str: return 'CT'

    custom_settings = dict(
        CONCURRENT_REQUESTS=10,
        ITEM_PIPELINES={"scraping_service.pipelines.DocumentSavePipeline": 300}  # download PDFs
    )
