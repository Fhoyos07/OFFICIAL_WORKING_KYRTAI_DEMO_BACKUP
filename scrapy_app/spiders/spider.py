from scrapy import Spider
from scrapy.http import Request, FormRequest, TextResponse
from datetime import date, datetime, timedelta
from http.cookies import SimpleCookie
import twocaptcha

import os
from ..utils.scrapy.decorators import log_response, save_response
from ..utils.file import load_json, save_json, load_csv
from ..utils.scrapy.url import parse_url_params
from ..settings import (CACHE_JSON_PATH, INPUT_CSV_PATH, DAYS_BACK,
                        TWO_CAPTCHA_API_KEY, TWO_CAPTCHA_SITE_KEY, MAX_CAPTCHA_RETRIES)


class CourtsNySpider(Spider):
    name = 'courts_ny'

    custom_settings = dict(
        CONCURRENT_REQUESTS=1,  # only 1 parallel request! don't change this
        DOWNLOAD_DELAY=0,
        DEPTH_PRIORITY=-100,
        ITEM_PIPELINES={
            "scrapy_app.pipelines.DocumentDownloadPipeline": 300,  # download PDFs in pipeline
            "scrapy_app.pipelines.CsvOnClosePipeline": 500,  # save Cases and Documents in CSV
        }
    )

    def __init__(self):
        # parse input CSV
        self.QUERIES = [row['Competitor / Fictitious LLC Name'].strip() for row in load_csv(INPUT_CSV_PATH)][:100]

        # min case date to crawl
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)

        # captcha settings
        self.solver = twocaptcha.TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, MAX_CAPTCHA_RETRIES

        # get session values from cache
        self._session_id = None
        self._recaptcha_code = None
        self._load_session_from_cache()
        super().__init__()

    def start_requests(self):
        for company in self.QUERIES:
            yield self.make_search_request(company)

    def make_search_request(self, company: str) -> Request:
        """
        Make direct POST search request for current company
        """
        self.logger.info(f"Starting search requests for {company}")

        # fallback if no cached session stored in json
        if not self._session_id or not self._recaptcha_code:
            self.logger.info(f"No session_id or captcha found. Open standard search form.")

            return Request(url='https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name',
                           callback=self.parse_search_form,
                           cb_kwargs=dict(company=company))

        # send search company
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        cookies = {'JSESSIONID': self._session_id}
        data = {
            "txtBusinessOrgName": company,
            "recaptcha-is-invisible": "true",
            "rbnameType": "partyName",
            "txtPartyFirstName": "",
            "txtPartyMiddleName": "",
            "txtPartyLastName": "",
            "g-recaptcha-response": self._recaptcha_code,
            "txtCounty": "-1",
            "txtCaseType": "",
            "txtFilingDateFrom": "",
            "txtFilingDateTo": "",
            "btnSubmit": "Search"
        }
        self.logger.debug(f"cookies: {cookies}")
        self.logger.debug(f"data: {data}")
        return FormRequest(url='https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name',
                           headers=headers,
                           cookies=cookies,
                           formdata=data,
                           callback=self.parse_cases,
                           cb_kwargs=dict(company=company),
                           dont_filter=True)

    @log_response
    def parse_search_form(self, response: TextResponse, company: str):
        """
        Search Form main page (opened only if no cached session_id). Set company and submit.
        """
        # parse cookies and extract JSESSIONID
        if not self._session_id:
            cookie = SimpleCookie()
            for cookie_item in response.headers.getlist('Set-Cookie'):
                cookie.load(cookie_item.decode('utf-8'))
            self._session_id = cookie['JSESSIONID'].value

        return FormRequest.from_response(response=response,
                                         formname='form',
                                         formdata={'txtBusinessOrgName': company},
                                         callback=self.parse_captcha_page,
                                         cb_kwargs=dict(company=company))

    @log_response
    def parse_captcha_page(self, response: TextResponse, company: str):
        """
        Captcha page. Solve using 2captcha and submit code.
        """
        self._recaptcha_code = self._get_captcha_response_code(url=response.url)
        yield FormRequest.from_response(response=response,
                                        formname='captcha_form',
                                        formdata={'g-recaptcha-response': self._recaptcha_code},
                                        callback=self.parse_after_captcha,
                                        cb_kwargs=dict(company=company))

    @log_response
    def parse_after_captcha(self, response: TextResponse, company: str):
        """
        Page opened after captcha submission. Save captcha code to json cache and retry search request.
        """
        self._save_session_to_cache()
        yield self.make_search_request(company)

    @log_response
    def parse_cases(self, response: TextResponse, company: str):
        """
        Page with cases search results (unsorted). Set sort by filling date desc and submit.
        """
        captcha_form = response.xpath('//form[@name="captcha_form"]')
        if captcha_form:
            self.logger.info(f"Captcha found.")
            yield from self.parse_captcha_page(response, company=company)
            return

        data = {
            'courtType': '',
            'selSortBy': 'FilingDateDesc',
            'btnSort': 'Sort'
        }
        yield FormRequest(url=response.url,
                          formdata=data,
                          callback=self.parse_sorted_cases,
                          cb_kwargs=dict(company=company),
                          dont_filter=True)

    @log_response
    def parse_sorted_cases(self, response: TextResponse, company: str):
        """
        Page with cases search results (sorted).
        """
        result_rows = response.css('.NewSearchResults tbody tr')
        self.logger.info(f'{company}: {len(result_rows)} total rows')

        date_before_threshold_found = False
        case_items = []
        for tr in result_rows:
            first_cell_texts: list[str] = tr.xpath('td[1]//text()[normalize-space()]').getall()
            case_number, date_str = first_cell_texts

            # compare date with threshold
            date_obj = datetime.strptime(date_str.strip(), '%m/%d/%Y').date()
            is_old = date_obj < self.MIN_DATE
            self.logger.info(f"{company}: Found case #{case_number} from {date_str.strip()}. is_old={is_old}")
            if is_old:
                date_before_threshold_found = True
                continue

            # find case_url
            case_url = tr.xpath('td[1]/a/@href').get()
            if not case_url:
                self.logger.error(f'Invalid case_url {case_url} at {response.url}')
                continue

            case_item = {
                "_item_type": 'Case',
                "Company": company,
                "Date": date_obj.isoformat(),
                "Case Number": case_number,
                "eFiling Status": tr.xpath('td[2]/text()').get(default='').strip(),
                "Case Status": tr.xpath('td[2]/span/text()').get(),
                "Caption": tr.xpath('td[3]/text()').get(),
                "Court": tr.xpath('td[4]/text()').get(default='').strip(),
                "Case Type": tr.xpath('td[4]/span/text()').get(),
                "URL": response.urljoin(case_url)
            }
            # return case item to csv
            case_items.append(case_item)
            yield case_item

            # crawl case page to parse documents
            yield response.follow(case_url, callback=self.parse_case, cb_kwargs=dict(case_number=case_number))

        # return company item to csv
        company_item = {
            "_item_type": 'Company',
            "Company": company,
            "Cases Total": len(result_rows),
            f"Cases in Last {DAYS_BACK} Days": len(result_rows),
            "Newest Date": case_items[0]['Date'] if case_items else None
        }
        yield company_item

        if result_rows and not date_before_threshold_found:
            next_page_url = response.xpath('//span[contains(@class,"pageNumbers")]/a[text()=">>"]/@href').get()
            yield response.follow(next_page_url, callback=self.parse_sorted_cases, cb_kwargs=dict(company=company))

    @log_response
    def parse_case(self, response, case_number: str):
        for document_tr in response.css('table.NewSearchResults tbody tr'):
            document_item = {
                '_item_type': 'Document',
                'Case Number': case_number,
            }
            document_url = document_tr.xpath('td[2]/a/@href').get()
            if not document_url:
                self.logger.warning(f'Invalid document_url: {document_url} at {response.url}')
                continue

            document_item['Document URL'] = response.urljoin(document_url)
            document_item['Document Name'] = document_tr.xpath('td[2]/a/text()').get()
            document_item['Document ID'] = parse_url_params(document_url)['docIndex'].strip('/').replace('/', '_')

            status_document_url = document_tr.xpath('td[4]/a/@href').get()
            if status_document_url:
                document_item['Status Document URL'] = response.urljoin(status_document_url)
                document_item['Status Document Name'] = document_tr.xpath('td[4]/a/text()').get()
            yield document_item

    def _save_session_to_cache(self):
        session_cache = dict(
            session_id=self._session_id,
            recaptcha_code=self._recaptcha_code
        )
        save_json(data=session_cache, file_path=CACHE_JSON_PATH)
        self.logger.info(f'Saved session to {CACHE_JSON_PATH}')

    def _load_session_from_cache(self):
        if not os.path.exists(CACHE_JSON_PATH):
            return
        session_cache = load_json(CACHE_JSON_PATH)
        self._session_id = session_cache['session_id']
        self._recaptcha_code = session_cache['recaptcha_code']

    def _get_captcha_response_code(self, url: str) -> str:
        self.current_captcha_retries += 1
        self.logger.info(f'Captcha solving try {self.current_captcha_retries} of {self.max_captcha_retries}')

        try:
            self.logger.info(f"Started solving captcha for {url}\nPlease wait.")
            result = self.solver.recaptcha(sitekey=TWO_CAPTCHA_SITE_KEY,
                                           url=url,
                                           # invisible=1,
                                           enterprise=1)
        except twocaptcha.api.ApiException as e:
            self.logger.info(str(e))
            if self.current_captcha_retries >= self.max_captcha_retries:
                raise ValueError(f"Max {self.current_captcha_retries} Captcha Retries reached")

            return self._get_captcha_response_code(url)

        self.current_captcha_retries = 0
        return result['code']


# class CourtsNyFileSpider(Spider):
#     name = 'courts_ny'
#
#     custom_settings = dict(
#         CONCURRENT_REQUESTS=15,  # only 1 parallel request! don't change this
#         DOWNLOAD_DELAY=0,
#         DEPTH_PRIORITY=-100,
#         ITEM_PIPELINES={
#             "scrapy_app.pipelines.DocumentDownloadPipeline": 300,  # download PDFs in pipeline
#             "scrapy_app.pipelines.CsvOnClosePipeline": 500,  # save Cases and Documents in CSV
#         }
#     )
