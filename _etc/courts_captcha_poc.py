import twocaptcha.api
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from parsel import Selector

TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'


class SolverPOC:
    def __init__(self):
        self.solver = TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, 3

        # selenium options
        options = Options()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--verbose")
        options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)

    def run(self, query: str):
        # open search page
        self.driver.get(f'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name')

        # populate search query and click button (don't use form.submit, cause empty page after solving captcha)
        form = self.driver.find_element(By.NAME, 'form')
        company_input = form.find_element(By.NAME, 'txtBusinessOrgName')
        company_input.send_keys(query)
        button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-action="submit"]')
        button.click()

        # solve captcha using 2captcha
        self.solve_captcha()

        response = Selector(text=self.driver.page_source)
        result_rows = response.css('.NewSearchResults tbody tr')
        print(f'{len(result_rows)} total rows')
        for result_row in result_rows:
            url = result_row.xpath('td[1]/a/@href').get()
            print(url)

        # process results...
        input('Continue?')

    def solve_captcha(self) -> None:
        captcha_code = self.get_captcha_response_code(url=self.driver.current_url)
        print(f"Captcha Response Code: {captcha_code}")

        # insert captcha into g-recaptcha-response textarea and submit form
        form = self.driver.find_element(By.NAME, 'captcha_form')
        textarea = form.find_element(By.NAME, 'g-recaptcha-response')
        self.driver.execute_script("arguments[0].value = arguments[1];", textarea, captcha_code)
        form.submit()

    def get_captcha_response_code(self, url) -> str:
        self.current_captcha_retries += 1
        print(f'Captcha solving try #{self.current_captcha_retries}')

        try:
            print(f"Started solving catpcha for {url}\nPlease wait.")
            result = self.solver.recaptcha(sitekey='6LdiezYUAAAAAGJqdPJPP7mAUgQUEJxyLJRUlvN6',
                                           url=url,
                                           invisible=1,
                                           enterprise=1)
        except twocaptcha.api.ApiException as e:
            print(str(e))
            if self.current_captcha_retries >= self.max_captcha_retries:
                raise ValueError(f"Max {self.current_captcha_retries} Captcha Retries reached")

            return self.get_captcha_response_code(url)

        self.current_captcha_retries = 0
        return result['code']


if __name__ == '__main__':
    SolverPOC().run(query='J.G. Wentworth Originations, LLC')
