from scrapy.http import Request, FormRequest, TextResponse

from utils.scrapy.response import extract_text_from_el
from utils.scrapy.decorators import log_response
from utils.scrapy.url import parse_url_params
from datetime import datetime, date
import re

from utils.scrapy.decorators import update_progress

from ._base import BaseCaseDetailSpider, BaseCaseSearchSpider, BaseDocumentDownloadSpider
from apps.web.models import Company, Case, CaseDetailsCT, Document, DocumentDetailsCT
from scraping_service.items import DbItem


class CtCaseSearchSpider(BaseCaseSearchSpider):
    """Step 1 - search companies for new cases"""
    name = 'ct_case_search'

    @property
    def state_code(self) -> str: return 'CT'

    @property
    def case_detail_relation(self): return 'ct_details'

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("CONCURRENT_REQUESTS",  value=10, priority='spider')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        result_rows = response.css('table.grdBorder .grdRow, table.grdBorder .grdRowAlt')
        self.logger.info(f'{name_variation} ({company.id}): Found {len(result_rows)} cases')

        for tr in result_rows:
            case_url = tr.xpath('td[3]/a/@href').get()
            if not case_url:
                self.logger.info(f'{name_variation} ({company.id}): Skipping as no case_url')
                continue

            # avoid scraping same case twice
            docket_id = parse_url_params(case_url)['DocketNo'].replace('-', '')
            if docket_id in self.existing_docket_ids:
                self.logger.debug(f'{name_variation} ({company.id}): Skipping existing case {docket_id}')
                continue
            self.existing_docket_ids.add(docket_id)

            case = Case(
                state=self.state,
                company=company,
                company_name_variation=name_variation,
            )
            case.ct_details = CaseDetailsCT()

            case.docket_id = docket_id
            case.case_number = extract_text_from_el(tr.xpath('td[3]'))
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


class CtCaseDetailSpider(BaseCaseDetailSpider):
    """Step2 - Open each case and save document urls"""
    name = 'ct_case_detail'

    @property
    def state_code(self): return 'CT'

    @property
    def case_detail_relation(self): return 'ct_details'

    @property
    def document_detail_relation(self): return 'ct_details'

    def start_requests(self):
        for case in self.cases_to_scrape:
            yield Request(case.url, callback=self.parse_case, cb_kwargs=dict(case=case), dont_filter=True)

    @update_progress
    def parse_case(self, response, case: Case):
        if '/ErrorPage.aspx' in response.url:
            self.logger.warning(f'Invalid url for case {case.id}: {response.url} (expected {response.request.url})')
            return

        # update case (scraped_date and is_scraped are updated in pipeline)
        case.filed_date = self.get_date_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblFileDate')
        if not case.filed_date:
            self.logger.warning(f'Filed date is invalid at {response.url}')
            return

        case.case_date = case.filed_date
        case.caption = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblCaseCaption')
        case.court = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailBasicInfo1_lblBasicLocation')
        case.case_type = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblCaseType')

        case.ct_details.prefix = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblPrefixSuffix')
        case.ct_details.return_date = self.get_date_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblReturnDate')
        case.ct_details.last_action_date = self.get_date_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailHeader1_lblReturnDate')

        case.ct_details.list_type = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailBasicInfo1_lblBasicListType')
        case.ct_details.list_claim_date = self.get_date_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailBasicInfo1_lblKeyTrialList')

        case.ct_details.judge = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailBasicInfo1_lblBasicDispJudge')
        case.ct_details.disposition = self.get_text_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailBasicInfo1_lblBasicDisposition')
        case.ct_details.disposition_date = self.get_date_by_id(response, 'ctl00_ContentPlaceHolder1_CaseDetailBasicInfo1_lblBasicDispositionDate')
        yield DbItem(record=case)

        # find documents
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
            document.ct_details = DocumentDetailsCT()

            document.unique_id = document_id
            document.name = tr.xpath('td[4]/a/text()').get()
            document.url = response.urljoin(document_url)

            # CT-specific fields
            document.ct_details.entry_no = extract_text_from_el(tr.xpath('td[1]'))

            file_date = extract_text_from_el(tr.xpath('td[2]'))
            document.ct_details.filed_date = datetime.strptime(file_date, "%m/%d/%Y").date()

            document.ct_details.filed_by = extract_text_from_el(tr.xpath('td[3]'))
            document.ct_details.arguable = extract_text_from_el(tr.xpath('td[5]'))
            yield DbItem(record=document)

    @staticmethod
    def get_text_by_id(response, el_id: str) -> str | None:
        value = response.xpath(f'//*[@id="{el_id}"]/text()[normalize-space()]').get()
        if value:
            return value.strip()

    def get_date_by_id(self, response, el_id: str) -> date | None:
        date_str = self.get_text_by_id(response, el_id)
        if date_str:
            return datetime.strptime(date_str, "%m/%d/%Y").date()


class CtDocumentSpider(BaseDocumentDownloadSpider):
    """Step 3 - download each document"""
    name = 'ct_documents'

    @property
    def state_code(self) -> str: return 'CT'
