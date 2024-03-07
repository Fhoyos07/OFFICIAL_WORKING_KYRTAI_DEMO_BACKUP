from scrapy.http import Request, FormRequest, TextResponse
import re

from utils.scrapy.response import extract_text_from_el
from utils.scrapy.decorators import log_response
from utils.scrapy.url import parse_url_params
from ._base import BaseCaseSearchSpider, BaseDocumentDownloadSpider

from datetime import datetime
from scraping_service.items import CaseItem, CaseItemCT, DocumentItem, DocumentItemCT


# Step 1 - search each company
class KyrtCtSearchSpider(BaseCaseSearchSpider):
    name = 'kyrt_ct_search'
    custom_settings = dict(
        CONCURRENT_REQUESTS=1,  # only 1 parallel request! don't change this
        ITEM_PIPELINES={"scraping_service.pipelines.CsvPipeline": 500}
    )

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
        for company in self.QUERIES:
            yield FormRequest.from_response(
                response=response,
                formxpath='//form[@name="aspnetForm"]',
                formdata={
                    'ctl00$ContentPlaceHolder1$txtLastName': company,
                    'ctl00$ContentPlaceHolder1$ddlLastNameSearchType': self.search_mode
                },
                callback=self.parse_cases,
                cb_kwargs=dict(company=company),
                dont_filter=True
            )

    # @log_response
    def parse_cases(self, response: TextResponse, company: str, page: int = 1):
        # if page == 1:
        #     count_of_records = response.xpath('//*[@id="ctl00_ContentPlaceHolder1_lblRecords"]/text()').get()
        #     company_item = {
        #         "_type": 'Companies',
        #         "Company": company,
        #         "Cases Total": count_of_records.split(' of ')[-1] if count_of_records else 0
        #     }
        #     yield company_item

        result_rows = response.css('table.grdBorder .grdRow, table.grdBorder .grdRowAlt')
        self.logger.info(f'{company}: Found {len(result_rows)} cases')
        for tr in result_rows:
            case_url = tr.xpath('td[3]/a/@href').get()
            if not case_url:
                continue
            case_id = parse_url_params(case_url)['DocketNo']

            # avoid scraping same case twice
            # if case_id in self.existing_case_ids:
            #     continue
            # self.existing_case_ids.add(case_id)

            case = CaseItem(state_specific_info=CaseItemCT())
            case.case_id = case_id
            case.company = company
            case.case_number = extract_text_from_el(tr.xpath('td[3]'))
            case.case_type = None  # populated in the next spider
            case.court = extract_text_from_el(tr.xpath('td[4]'))
            case.url = response.urljoin(case_url)

            case.state_specific_info.case_name = extract_text_from_el(tr.xpath('td[2]'))
            case.state_specific_info.party_name = extract_text_from_el(tr.xpath('td[1]'))
            case.state_specific_info.pty_number = extract_text_from_el(tr.xpath('td[5]'))
            case.state_specific_info.self_rep = extract_text_from_el(tr.xpath('td[6]'))
            yield Request(url=case.url,
                          callback=self.parse_case,
                          cb_kwargs=dict(case=case))

        pagination_table = response.css('.grdBorder tr:nth-child(1) table tr')
        next_page_url = pagination_table.xpath('td[span]/following-sibling::td[1]/a/@href').get()
        if next_page_url:
            action, param = re.findall(r"__doPostBack\('(.+)','(.+)'\)", next_page_url)[0]
            yield FormRequest.from_response(response=response,
                                            formxpath='//form[@name="aspnetForm"]',
                                            formdata={
                                                '__EVENTTARGET': action,
                                                '__EVENTARGUMENT': param
                                            },
                                            callback=self.parse_cases,
                                            cb_kwargs=dict(company=company, page=page+1),
                                            dont_filter=True)
        else:
            self.progress_bar.update()

    @log_response
    def parse_case(self, response, case: CaseItem):
        case.state_specific_info.prefix = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblPrefixSuffix')
        case.case_type = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblCaseType')

        case_file_date_str = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblFileDate')
        file_date = datetime.strptime(case_file_date_str, "%m/%d/%Y").date()
        case.file_date = file_date.isoformat()

        return_date = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblReturnDate')
        case.state_specific_info.return_date = datetime.strptime(return_date, "%m/%d/%Y").date()
        yield case

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

            document = DocumentItem(state_specific_info=DocumentItemCT())

            document.url = response.urljoin(document_url)
            document.company = case.company
            document.case = case.case_number
            document.name = tr.xpath('td[4]/a/text()').get()
            document.document_id = parse_url_params(document_url)['DocumentNo']

            document.state_specific_info.entry_no = extract_text_from_el(tr.xpath('td[1]'))

            file_date = extract_text_from_el(tr.xpath('td[2]'))
            document.state_specific_info.file_date = datetime.strptime(file_date, "%m/%d/%Y").date()

            document.state_specific_info.filed_by = extract_text_from_el(tr.xpath('td[3]'))
            document.state_specific_info.arguable = extract_text_from_el(tr.xpath('td[5]'))
            yield document

    @staticmethod
    def extract_header(response, attr_id: str) -> str | None:
        value = response.xpath(f'//*[@id="{attr_id}"]/text()').get()
        if value:
            return value.strip()


# Step 2 - open and download each document
class KyrtCtDocumentSpider(BaseDocumentDownloadSpider):
    name = 'kyrt_ct_documents'
    @property
    def state_code(self) -> str: return 'CT'

    custom_settings = dict(
        CONCURRENT_REQUESTS=10,
        ITEM_PIPELINES={"scraping_service.pipelines.DocumentSavePipeline": 300}  # download PDFs
    )
