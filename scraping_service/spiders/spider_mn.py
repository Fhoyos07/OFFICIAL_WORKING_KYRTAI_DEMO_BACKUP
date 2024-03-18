from scrapy.http import Request, FormRequest, TextResponse

from utils.scrapy.response import extract_text_from_el
from utils.scrapy.decorators import log_response
from utils.scrapy.url import parse_url_params
from datetime import datetime
import re

from utils.scrapy.decorators import update_progress

from ._base import BaseCaseDetailSpider, BaseCaseSearchSpider, BaseDocumentDownloadSpider
from apps.web.models import Company, Case, CaseDetailsMN, Document, DocumentDetailsMN
from scraping_service.items import DbItem


class MnCaseSearchSpider(BaseCaseSearchSpider):
    """Step 1 - search companies for new cases"""
    name = 'mn_case_search'

    @property
    def state_code(self) -> str: return 'MN'

    @property
    def case_detail_relation(self): return 'mn_details'

    def start_requests(self):
        # todo: https://publicaccess.courts.state.mn.us/CaseSearch
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
        result_rows = response.css('table.grdBorder .grdRow, table.grdBorder .grdRowAlt')
        self.logger.info(f'{name_variation} ({company.id}): Found {len(result_rows)} cases')

        for tr in result_rows:
            case_url = tr.xpath('td[3]/a/@href').get()
            if not case_url:
                self.logger.info(f'{name_variation} ({company.id}): Skipping as no case_url')
                continue

            # avoid scraping same case twice
            docket_id = parse_url_params(case_url)['DocketNo']
            if docket_id in self.existing_docket_ids:
                self.logger.debug(f'{name_variation} ({company.id}): Skipping existing case {docket_id}')
                continue
            self.existing_docket_ids.add(docket_id)

            case = Case(
                state=self.state,
                company=company,
                company_name_variation=name_variation,
            )
            case.ct_details = CaseDetailsMN()

            case.docket_id = docket_id
            case.case_number = extract_text_from_el(tr.xpath('td[3]'))
            case.case_type = None  # populated in the next spider
            case.court = extract_text_from_el(tr.xpath('td[4]'))
            case.caption = extract_text_from_el(tr.xpath('td[2]'))

            case.url = response.urljoin(case_url)

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


class MnCaseDetailSpider(BaseCaseDetailSpider):
    """Step2 - Open each case and save document urls"""
    name = 'mn_case_detail'

    @property
    def state_code(self): return 'MN'

    @property
    def case_detail_relation(self): return 'mn_details'

    @property
    def document_detail_relation(self): return 'mn_details'

    def start_requests(self):
        for case in self.cases_to_scrape:
            yield Request(case.url, callback=self.parse_case, cb_kwargs=dict(case=case), dont_filter=True)

    @update_progress
    def parse_case(self, response, case: Case):
        if '/ErrorPage.aspx' in response.url:
            self.logger.warning(f'Invalid url for case {case.id}: {response.url} (expected {response.request.url})')
            return

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

            # avoid scraping same document twice
            document_id = parse_url_params(document_url)['DocumentNo']
            if document_id in self.existing_document_ids:
                self.logger.debug(f'Case #{case.docket_id}: Skipping existing document {document_id}')
                continue

            document = Document(case=case)
            document.ct_details = DocumentDetailsMN()

            document.document_id = document_id
            document.name = tr.xpath('td[4]/a/text()').get()
            document.url = response.urljoin(document_url)

            # CT-specific fields
            document.ct_details.entry_no = extract_text_from_el(tr.xpath('td[1]'))

            file_date = extract_text_from_el(tr.xpath('td[2]'))
            document.ct_details.filed_date = datetime.strptime(file_date, "%m/%d/%Y").date()

            document.ct_details.filed_by = extract_text_from_el(tr.xpath('td[3]'))
            document.ct_details.arguable = extract_text_from_el(tr.xpath('td[5]'))
            yield DbItem(record=document)

        # update case (scraped_date and is_scraped are updated in pipeline)
        case.case_type = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblCaseType')
        case.ct_details.prefix = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblPrefixSuffix')

        file_date_str = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblFileDate')
        case.filed_date = datetime.strptime(file_date_str, "%m/%d/%Y").date()

        return_date_str = self.extract_header(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblReturnDate')
        case.ct_details.return_date = datetime.strptime(return_date_str, "%m/%d/%Y").date()
        yield DbItem(record=case)

    @staticmethod
    def extract_header(response, attr_id: str) -> str | None:
        value = response.xpath(f'//*[@id="{attr_id}"]/text()').get()
        if value:
            return value.strip()


class MnDocumentSpider(BaseDocumentDownloadSpider):
    """Step 3 - download each document"""
    name = 'mn_documents'

    @property
    def state_code(self) -> str: return 'MN'
