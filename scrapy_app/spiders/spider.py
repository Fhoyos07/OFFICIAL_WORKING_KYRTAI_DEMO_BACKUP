from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, FormRequest, TextResponse
from datetime import date, datetime, timedelta
from http.cookies import SimpleCookie
from pathlib import Path
from tqdm import tqdm
import twocaptcha
import sys
import os

from ..utils.scrapy.decorators import log_response, save_response, log_method
from ..utils.file import load_json, save_json, load_csv
from ..utils.scrapy.url import parse_url_params
from ..settings import (USE_CACHE, CACHE_JSON_PATH, INPUT_CSV_PATH, FILES_DIR, DAYS_BACK, MAX_COMPANIES,
                        TWO_CAPTCHA_API_KEY, MAX_CAPTCHA_RETRIES)


# Step 1 - search each company
class KyrtNySearchSpider(Spider):
    name = 'kyrt_ny_search'
    custom_settings = dict(
        CONCURRENT_REQUESTS=1,  # only 1 parallel request! don't change this
        ITEM_PIPELINES={"scrapy_app.pipelines.CsvPipeline": 500}  # save Cases and Companies to CSV
    )
    state_code = 'NY'

    def __init__(self):
        # parse input CSV
        companies = [row['Competitor / Fictitious LLC Name'] for row in load_csv(INPUT_CSV_PATH)]
        companies = [c.strip().upper().replace(', LLC', ' LLC') for c in companies]
        if MAX_COMPANIES:
            companies = companies[:MAX_COMPANIES]
            self.logger.info(f"Cut companies to only {MAX_COMPANIES} first")
        self.logger.info(f"Before deduplication: {len(companies)} companies")

        self.QUERIES = sorted(list(set(c for c in companies if c)))
        self.logger.info(f"After deduplication: {len(self.QUERIES)} companies")

        # set up progress bar
        self.progress_bar = tqdm(total=len(self.QUERIES), file=sys.stdout, leave=False)

        # min case date to crawl
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)

        # captcha settings
        self.solver = twocaptcha.TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.recaptcha_sitekey = '6LdiezYUAAAAAGJqdPJPP7mAUgQUEJxyLJRUlvN6'  # don't change
        self.current_captcha_retries, self.max_captcha_retries = 0, MAX_CAPTCHA_RETRIES

        # get session values from cache
        self._session_id = None
        self._recaptcha_code = None
        if USE_CACHE:
            self._load_session_from_cache()

        # collect existing ids to avoid scraping same case twice
        self.existing_case_ids = set()
        super().__init__()

    def start_requests(self):
        yield self.process_next_company()

    def process_next_company(self):
        if not self.QUERIES:
            self.logger.info(f"Finished")
            return

        company_name = self.QUERIES.pop(0)
        return self.make_search_request(company_name)

    def make_search_request(self, company_name: str) -> Request:
        """
        Make direct POST search request for current company
        """
        # fallback if no cached session stored in json
        if not self._session_id or not self._recaptcha_code:
            self.logger.info(f"No session_id or captcha found. Opening standard search form.")

            return Request(url='https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name',
                           callback=self.parse_search_form,
                           cb_kwargs=dict(company=company_name),
                           dont_filter=True)

        # don't use filter by date
        # today = date.today()
        # date_from, date_to = today - timedelta(days=DAYS_BACK), today + timedelta(days=1)

        # send search company
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        cookies = {'JSESSIONID': self._session_id}
        data = {
            "txtBusinessOrgName": company_name,
            "recaptcha-is-invisible": "true",
            "rbnameType": "partyName",
            "txtPartyFirstName": "",
            "txtPartyMiddleName": "",
            "txtPartyLastName": "",
            "g-recaptcha-response": self._recaptcha_code,
            "txtCounty": "-1",
            "txtCaseType": "",
            "txtFilingDateFrom": "",    # date_from.strftime("%m/%d/%Y"),
            "txtFilingDateTo": "",      # date_to.strftime("%m/%d/%Y"),
            "btnSubmit": "Search",

        }
        self.logger.debug(f"cookies: {cookies}")
        self.logger.debug(f"data: {data}")
        return FormRequest(url='https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name',
                           headers=headers,
                           cookies=cookies,
                           formdata=data,
                           callback=self.parse_cases,
                           cb_kwargs=dict(company=company_name),
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
                                         cb_kwargs=dict(company=company),
                                         dont_filter=True)

    def parse_captcha_page(self, response: TextResponse, company: str):
        """
        Captcha page. Solve using 2captcha and submit code.
        """
        self._recaptcha_code = self._get_captcha_response_code(url=response.url)
        yield FormRequest.from_response(response=response,
                                        formname='captcha_form',
                                        formdata={'g-recaptcha-response': self._recaptcha_code},
                                        callback=self.parse_after_captcha,
                                        cb_kwargs=dict(company=company),
                                        dont_filter=True)

    @log_response
    def parse_after_captcha(self, response: TextResponse, company: str):
        """
        Page opened after captcha submission. Save captcha code to json cache and retry search request.
        """
        self._save_session_to_cache()
        yield self.make_search_request(company)

    # @log_response
    def parse_cases(self, response: TextResponse, company: str):
        """
        Page with cases search results
        """
        self.logger.info(f"{company}: Opened CASES page")
        captcha_form = response.xpath('//form[@name="captcha_form"]')
        if captcha_form:
            self.logger.info(f"{company}: Captcha found.")
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

    def parse_sorted_cases(self, response: TextResponse, company: str, page: int = 1):
        self.logger.info(f"{company}: Opened SORTED CASES page #{page}")
        result_rows = response.css('.NewSearchResults tbody tr')
        search_title = response.css('.Document_Row strong::text').get()
        self.logger.info(f'{company}: Search results page for {search_title}: {len(result_rows)} rows')

        date_before_threshold_found = False
        case_items = []
        newest_date = None

        for tr in result_rows:
            # parse case number and date
            first_cell_texts: list[str] = tr.xpath('td[1]//text()[normalize-space()]').getall()
            case_number, date_str = first_cell_texts
            date_obj = datetime.strptime(date_str.strip(), '%m/%d/%Y').date()
            is_old = date_obj < self.MIN_DATE
            self.logger.info(f"{company}: Found case #{case_number} from {date_str.strip()}. is_old={is_old}")

            if not newest_date:  # save newest_date for company stats
                newest_date = date_obj

            if is_old:           # compare date with threshold
                date_before_threshold_found = True
                continue

            # find case_url
            case_url = tr.xpath('td[1]/a/@href').get()
            if not case_url:
                self.logger.error(f'Invalid case_url {case_url} at {response.url}')
                continue

            # don't re-scrape same case twice
            case_id = parse_url_params(case_url)['docketId']
            if case_id in self.existing_case_ids:
                continue

            self.existing_case_ids.add(case_id)

            case_item = {
                "_type": 'Cases',
                "Case Id": case_id,
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

        # return company item to csv
        if page == 1:
            results_count, items_count = len(result_rows), len(case_items)
            company_item = {
                "_type": 'Companies',
                "Company": company,
                "Cases Total": results_count if results_count < 25 else f'{results_count}+',
                f"Cases in Last {DAYS_BACK} Days": items_count if items_count < 25 else f'{items_count}+',
                "Newest Date": newest_date.isoformat() if newest_date else None
            }
            yield company_item

        next_page_url = response.xpath('//span[contains(@class,"pageNumbers")]/a[text()=">>"]/@href').get()
        if next_page_url and not date_before_threshold_found:
            yield response.follow(next_page_url,
                                  callback=self.parse_sorted_cases,
                                  cb_kwargs=dict(company=company, page=page+1),
                                  dont_filter=True)
        else:
            # finished scraping company
            self.progress_bar.update()
            yield self.process_next_company()

    def _save_session_to_cache(self):
        session_cache = dict(
            session_id=self._session_id,
            recaptcha_code=self._recaptcha_code
        )
        save_json(data=session_cache, file_path=CACHE_JSON_PATH)
        self.logger.info(f'Saved session to {CACHE_JSON_PATH}')

    def _load_session_from_cache(self):
        if not CACHE_JSON_PATH.exists():
            return
        session_cache = load_json(CACHE_JSON_PATH)
        self._session_id = session_cache['session_id']
        self._recaptcha_code = session_cache['recaptcha_code']
        self.logger.info(f"Loaded cached session from {CACHE_JSON_PATH}")

    def _get_captcha_response_code(self, url: str) -> str:
        self.current_captcha_retries += 1
        self.logger.info(f'Started captcha solving try {self.current_captcha_retries} of {self.max_captcha_retries} (url: {url})')

        try:
            result = self.solver.recaptcha(sitekey=self.recaptcha_sitekey,
                                           url=url,
                                           # invisible=1,
                                           enterprise=1)
        except twocaptcha.api.ApiException as e:
            self.logger.info(str(e))
            if self.current_captcha_retries >= self.max_captcha_retries:
                raise ValueError(f"Max {self.current_captcha_retries} Captcha Retries reached")

            return self._get_captcha_response_code(url)

        self.logger.info(f"Captcha solved!")
        self.current_captcha_retries = 0
        return result['code']


# Step2 - Open each case and save document urls
class KyrtNyCaseSpider(Spider):
    name = 'kyrt_ny_cases'
    state_code = 'NY'

    custom_settings = dict(
        CONCURRENT_REQUESTS=1,
        ITEM_PIPELINES={"scrapy_app.pipelines.CsvPipeline": 300}   # save documents to CSV
    )

    def __init__(self):
        super().__init__()

        cases_path: Path = FILES_DIR / self.state_code / f'cases.csv'
        self.cases: list[dict] = load_csv(cases_path) if cases_path.exists() else []
        self.logger.info(f"Found {len(self.cases)} cases to process")
        self.progress_bar = tqdm(total=len(self.cases), file=sys.stdout)

    def start_requests(self) -> Iterable[Request]:
        for case in self.cases:
            # crawl case page to parse documents
            yield Request(case['URL'], callback=self.parse_case, cb_kwargs=dict(case=case))

    def parse_case(self, response, case: dict):
        self.progress_bar.update()
        for document_tr in response.css('table.NewSearchResults tbody tr'):
            document_item = {
                '_type': 'Documents',
                'Company': case['Company'],
                'Case Number': case['Case Number'],
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


# Step 3 - open and download each document
class KyrtNyDocumentSpider(Spider):
    name = 'kyrt_ny_documents'
    state_code = 'NY'

    custom_settings = dict(
        CONCURRENT_REQUESTS=1,
        ITEM_PIPELINES={"scrapy_app.pipelines.DocumentSavePipeline": 300}  # download PDFs
    )

    def __init__(self):
        super().__init__()

        # parse input CSV
        self.document_name_by_url: dict[str, str] = {}
        cases_with_privacy_notices: set[str] = set()

        documents_path: Path = FILES_DIR / self.state_code / f'documents.csv'
        documents = load_csv(documents_path) if documents_path.exists() else []
        for row in documents:
            company, doc_id, case_number = row['Company'], row['Document ID'], row['Case Number']
            base_dir = f"{company.replace('/', '_')}/{case_number.replace('/', '_')}"

            # save url
            self.document_name_by_url[row['Document URL']] = f"{base_dir}/{doc_id.replace('/', '_')}.pdf"

            # add privacy notice only once per case
            if case_number in cases_with_privacy_notices:
                continue
            cases_with_privacy_notices.add(case_number)

            status_doc_slug = row['Status Document Name'].lower().replace(' ', '_')
            self.document_name_by_url[row['Status Document URL']] = f"{base_dir}/{status_doc_slug}.pdf"

        self.progress_bar = tqdm(total=len(self.document_name_by_url), file=sys.stdout, leave=False)

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
