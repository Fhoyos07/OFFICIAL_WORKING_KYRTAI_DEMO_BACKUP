from scrapy import Spider, Request, FormRequest
from datetime import date, datetime, timedelta
from twocaptcha import TwoCaptcha
import twocaptcha
from urllib.parse import *

import os
import requests
from ..items import DynamicItemLoader
from ..utils.scrapy.decorators import log_response, save_response, log_method

DAYS_BACK = 10
# CAPTCHA = '03AFcWeA7O12uLCiBFrMl8LAG2hqYKIUkECg5lv0gUCnzi738-RgRAU7v-H94OQC2liuxnLl885UYi8Omg5qH317pn-CurkM8DXcq8_k4FmFfrZpMI_Fca2Wr9-Gawpv31J1k7NGlFSZc0HUGD0IC5m_v4L_7l3199qxz-jHNsUL6q_WvwF6bSW63Ycg0B0JXVLnn04XZUG3COvFvcQBMGu9nF_awyrFwfbfc6QgrP0LMvYoKXT7YzGwncP-kwbMRdvaWNVRltwgF88EmhG3e2g3Nojmg-Fi4GLP8mw7VM6eEyUMZoQQGIBVgVQomqY0WfQH29punEeDKE84osKaCf8JlMQM9dFUe7uyioNZRNnXtxi1LfbGCxX4HQ862qToWBQoKakA9pUOssuwox6-HdUM7U92vdWweVYo8Z-ItD6eSY-_UB8gBnrvzzkVYgkCEO-Gp7visC9cSwAsTfbvntnCtN5GFdY2JhR0uxc3ZLBqkLGY99lhVvJz33CB_iXcWHPT5Kcs5y4FVFMiFch_dZWzIAoDzyDeWgG--ecdDkmyxjy6Sd6rRbgek6LPvKk5M5Rd1Hhrw5fTYDLd8btaQ08RkCGZg0nOY7mO0-coFoQagERmiUmpPBffuW6LqmME6WzFf4OQYuyV0W41I1K-ULvTkFA5cF6W1mWf1X0SIn_QD0gqFMQ9Y-f8JoTXiC8TDiYjpBtrGIOEvsgx0QZSHW4K1VS9D9PkGqESqN-9616Oy3VsM_xxmwngLNM_A8T_VfxSFvuO6EgPMpv1LURy84l_-eZqcE7fIb6c9tSJlSFYLuKkWEM4S82TTeioh3KcgPMRKvduDK8_tXFvwjGeHFXmKbQNi-tmXrwJP0GkUcmBXJiIkITwg3T1ObIP4dvcWY1Ofj_k0fNIAchwfBozJqILSjp_JcFRnV0lkF4hmqI9MU21cTzG52VbqTm_-Gan9hKVhDsmiQVukAaofnvyGwpEzauCa1KYQN02uoHw7fQFcBxjnwiVejvBl-kHzZFYN8tCT5vxwpXhEBFSaT-oWBFWqV-nENGMSRFfkPVyMJ80rY0yjoj7mSBE9uLpq0LSxEFkbRTM9_zQTzsuX13BfWTnwMvUYnkruREvNOO0Dfa-v7fLZ8SzytErNQdNd0ZNI3aSTz4P4ybYiu-WiOjeCX0bQngO3VD9ghBZgD9kq93aGyQKasUwtdX6axPqnUuXYmescEGf9XQO1OVzzS4PlBOmcnBHy2w6ChjMZRdS1mkMdqPzJMpXJJuN3zf-oCEOmbcEWAHSIMwkrYgeIkM9whW-QelESawZZrslQrX4Nz4Jok6yG-FLd8jZzNAgF3kah2UKI-M_oCCwWukEmfqoQGA305TsHX7Jz2drpXSo1u8fD5s-BbTQliuKnqRDJyQahc8mCjKIi5KgtGglQyI0SN_NvFpfqbTCjnkyKW0olLRrcm_ttcjy6jDCJUMr5hf4lftEujfedZPlQAN16Sb45c7UIi6qn3dPtnTnkKQHSsdyf4CBN0A1xSWjERwkMutmKJOjNYwpNYs5C-ItsFCS40JmDysmUXxH9x46-UBS8WXdUT-a3D-9lRHJHxaNH7XWoC9egzqKdwMRLc2fgiWr-chtIAD9xu1N97GS5f8SeKS_AS-0YYmtomJxuAegLD9PrQh-9LPiAKv4QWYSm4eN7oG82oBnAtVsLDi8gcu3D-L2eXn3SdOkpJKC5YLE5jos73ylKTK_iP-7L4UyrSzofDzBRpOsf1O2kqhG_If9OOUQM8bAioiAdll5Ri5aaY3vcut2mL9wfathAdO3G2xtTrUUxYwQzGguthY7fKDbEYndl5YCjiu8JoRDypd2IHknIVxVMyINnY9oBz'
TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
MAX_CAPTCHA_RETRIES = 7


class CourtsNySpider(Spider):
    name = 'courts_ny'
    custom_settings = dict(
        CONCURRENT_REQUESTS_PER_DOMAIN=1    # only 1 parallel request
    )

    def __init__(self):
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)
        self.solver = TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, MAX_CAPTCHA_RETRIES
        super().__init__()

    def start_requests(self):
        QUERY = "J.G. Wentworth Originations, LLC"
        url = 'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        SESSION_ID = 'E95A7E43939ADB65513E5800B0D006FD.server2085'

        # recaptcha = self.get_captcha_response_code(url='https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name')
        RECAPTCHA_CODE = '03AFcWeA5CQmAq2ZxarP-qTqP9pOaJmS2tVbU2YpMYMoSF_puzVkBbOUums-JPauYdhcnDOjZ_oDWjNeRIwJsS_d5JCRivr5a1vDyx-3Xu9dK7pS4SaPZ-heM5sGgZ-77uLvN9u_iVBYvwB1ZVmPDoC-PJkpVIF-u3M1CX1UzPWEJ-q3tWhJQDknN5QisYU1_ZMERYF7a7nU3J5d2WnlEPzoqT996kq1hbIcGuuwemeB1v7MdOEm13S0pK0cL1PZN-eVdMHWKX9xAIRgPzn_EQyaNKHQIFHJo2lBnhpwZanOrHb9nkihflnksn-XFgZn2rsCcTMIIZokMJf-xzfYprrC_qjBSyXY7M1KyOmVYVYCmYmKXdldJ05yvSt6HmUwPFdfvnP3-0e95k7jJxu5fR6xD8JhQFi_eGM0aF4_oSYDEUw6QhHvZ6FwwDKIoIOuNshwqNyxU58p0t-lAaPzpOK4Zgy-L0i0tg9lzS9UgNpNBiKDH2qXe71wBW0ntYPDRNR75hxrbepalAQo0KFayNZG7Gm8mqDenLf9oiTafr0dA-F5r_0WD1gEizUUBTnyeZ98tljK7nLV2njiwSW1zgGa37qcmTtVXm2FvL6tjBMEOVlyA2Ic5MfjLzx-_rcy2IALt1aygSegbNO0LPvyClvylsPtbaJa3w8wVg70NS1SK3Dz8zueCS7-KQ3YC0g56YYUN-v6PUkImS1B1HoNc8rjqgi1LitKn6MFB8LaYRB-AQqnama64v7idhu2dWqs1lhsngBrD5-O50bR7S3VyKeyvnFKU1GL2L_BnFSKUCoVRghVohDFDR_DZYeskAFRwPTZSMOE6GSTqQhDalOSeqNca-_sQ-PNiMgrwrweEbdGY47y5Yc3foCeCVl4n6V0-dxhho83bwyrJfY-fjAfxs5EIM77T_K18xxj_z7hrAMUDt_LDEYlbV5hkw_a_DWqaJfKUWfuoYpf1rdI2leFYShlw-BTFTwbHY9IvjOs8Ogzy2A69ub_ycUc8qWQyL9QY2ARrP1m4KkI415zpOWCjFfK3bCjBG6smi2u_OJSA_dYTCeI-QzWD6lhswg5WBRyAzI4OHvAztIlxADNuY2l239LbE1UTcZsFwO78p8aALfw4PWN4yWPaH_u-IYQvQT_CeWdkMcZIM-VLUN2cQSBmvFBvabq02vv2KV_FiAdbvTenpJhS8W8uaSPkAn7OVBp2hTO8J-yFXWApviYC83gVaBqv0jbulvYHCzWZsLzgwc14dsu8YP4hmcb820OHkBbbbtkoQQ_MLb-Rkn394KMHOZRp_PXgzeh9nGn_p8gpAObtz3NIgqfXGgUe0o2hPxxyLWT8b5zDmaxJ1BmrYb-L6Mv6KbU-JsXyY-5xZJb7WStq-9Oa09lNgiGNxmOA_ZIclNcHYUTL2pJwI1hAQTHDkLKrOeRN9MFp1QGzfecR2VFc3wP9Bjoyri5Pvp7dz-bR1bBSZiwux6Ad6VpT0szHtR4o1Q2qdSsQd4gTtLz7OqVMw5f51wJ3MSRI6W0bPMmkCwtGePXHfxIPgI9UfszVMm2c6nIdmf9DigRLX_L-brmaUwqkowIZUwGvMtTfxq5kcTUy3Ra_VXPFKA-YAQ75h04Z4CvZB-NufkUmT6bTAEXaS9XdfnlASkrcvcFrSn50CfFYLkg78_qELYnFSV6ZownBe0CjZbEcbbYsjo82o9WFuMRwj3UgVKhNDD8V-03vIWafLm6NjcVn2ygkK0pA8cYFrOPjB1vvUdwZt1i8RE_YIFmK2bWR8N0ayNm_4S8KBrOCpq9G-piR38fv8LIaGZx5oFwp1qzjYBlj2KOEA2Fkq44vrs_deUmUFmXBB-cVyXZo_RQBTjURAqM1sIO5Rw2lCMN3W3ovNIg'


        cookies = {'JSESSIONID': SESSION_ID}
        data = {
            "recaptcha-is-invisible": "true",
            "rbnameType": "partyName",
            "txtBusinessOrgName": QUERY,
            "txtPartyFirstName": "",
            "txtPartyMiddleName": "",
            "txtPartyLastName": "",
            "g-recaptcha-response": RECAPTCHA_CODE,
            "txtCounty": "-1",
            "txtCaseType": "",
            "txtFilingDateFrom": "",
            "txtFilingDateTo": "",
            "btnSubmit": "Search"
        }
        self.logger.info(f"urlencode(data): {urlencode(data)}")
        yield FormRequest(url=url, headers=headers, cookies=cookies, formdata=data, callback=self.parse_list, dont_filter=True)

    def get_captcha_response_code(self, url) -> str:
        self.current_captcha_retries += 1
        self.logger.info(f'Captcha solving try {self.current_captcha_retries} of {self.max_captcha_retries}')

        try:
            self.logger.info(f"Started solving catpcha for {url}\nPlease wait.")
            result = self.solver.recaptcha(sitekey='6LdiezYUAAAAAGJqdPJPP7mAUgQUEJxyLJRUlvN6',
                                           url=url,
                                           invisible=1,
                                           enterprise=1)
        except twocaptcha.api.ApiException as e:
            self.logger.info(str(e))
            if self.current_captcha_retries >= self.max_captcha_retries:
                raise ValueError(f"Max {self.current_captcha_retries} Captcha Retries reached")

            return self.get_captcha_response_code(url)

        self.current_captcha_retries = 0
        return result['code']

    @log_response
    @save_response
    def parse_list(self, response):
        data = {
            'courtType': '',
            'selSortBy': 'FilingDateDesc',
            'btnSort': 'Sort'
        }
        yield FormRequest(url=response.url, formdata=data, callback=self.parse_sorted_list, dont_filter=True)

    @log_response
    @save_response
    def parse_sorted_list(self, response):
        result_rows = response.css('.NewSearchResults tbody tr')
        self.logger.info(f'{len(result_rows)} total rows')

        old_date_found = False
        for tr in result_rows:
            first_cell_texts: list[str] = tr.xpath('td[1]//text()[normalize-space()]').getall()
            self.logger.info(f"first_cell_texts: {first_cell_texts}")

            date_obj = datetime.strptime(first_cell_texts[1].strip(), '%m/%d/%Y').date()
            if date_obj < self.MIN_DATE:
                old_date_found = True
                continue

            case_url = tr.xpath('td[1]/a/@href').get()
            if not case_url:
                self.logger.error(f'Invalid case_url at {response.url}')
                continue

            item = {
                "Date": date_obj.isoformat(),
                "Case Number": first_cell_texts[0],
                "eFiling Status": tr.xpath('td[2]/text()').get(default='').strip(),
                "Case Status": tr.xpath('td[2]/span/text()').get(),
                "Caption": tr.xpath('td[3]/text()').get(),
                "Court": tr.xpath('td[4]/text()').get(default='').strip(),
                "Case Type": tr.xpath('td[4]/span/text()').get(),
                "URL": response.urljoin(case_url)
            }
            self.logger.info(f"item: {item}")
            yield response.follow(case_url, callback=self.parse_case, cb_kwargs=dict(item=item))

        if not old_date_found:
            next_page_url = response.xpath('//span[contains(@class,"pageNumbers")]/a[text()=">>"]/@href').get()
            yield response.follow(next_page_url, callback=self.parse_sorted_list)

    def parse_case(self, response, item: dict):
        yield item

    def download_pdf(self, url, target_directory):
        # headers = {'User-Agent': USER_AGENT}
        doc_id = url.split('docId=')[-1]
        doc_id = doc_id.strip("/\\").replace("/", "_").replace("\\", "_")
        file_name = f"{doc_id}.pdf"

        target_subdir = os.path.normpath(os.path.join('pdfs', target_directory))
        if not os.path.exists(target_subdir):
            os.makedirs(target_subdir)

        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            pdf_path = os.path.join(target_subdir, file_name)
            with open(pdf_path, 'wb') as file:
                file.write(response.content)
            self.logger.info(f"Downloaded {file_name} to {target_subdir}")
            time.sleep(PDF_DOWNLOAD_DELAY)
        else:
            self.logger.error(f"Failed to download {url}. Status code: {response.status_code}")