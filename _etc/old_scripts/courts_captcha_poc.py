import twocaptcha.api
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from parsel import Selector

TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
SITE_KEY = '0f0ec7a6-d804-427d-8cfb-3cd7fad01f00'


class SolverPOC:
    def __init__(self):
        self.solver = TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, 3

        # selenium options
        options = Options()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--verbose")
        # options.add_argument("--headless")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--enable-javascript")

        self.driver = webdriver.Chrome(options=options)

    def run(self, query: str):
        # open search page
        self.driver.get(f'https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name')

        cookie = {
            'name': 'JSESSIONID',
            'value': 'E7BC76B10545C8887056E28FE2222A84.server2068',
            # Specify additional properties as needed, for example:
            'path': '/nyscef',
            # 'domain': 'iapps.courts.state.ny.us',  # Uncomment and replace with the domain if needed
            # 'secure': True,  # Uncomment if the cookie should be sent over HTTPS only
            'httpOnly': True,  # Uncomment if the cookie is HTTP onlym
            'priority': 'High'
        }

        # Adding the cookie to the current session
        self.driver.add_cookie(cookie)

        input('Continue?')
        #
        # # populate search query and click button (don't use form.submit, cause empty page after solving captcha)
        # form = self.driver.find_element(By.NAME, 'form')
        # company_input = form.find_element(By.NAME, 'txtBusinessOrgName')
        # company_input.send_keys(query)
        # button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-action="submit"]')
        # button.click()

        # solve captcha
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
        input('Solve Captcha Manually, then click Enter')
        return
        captcha_code = self.get_captcha_response_code(url=self.driver.current_url)
        print(f"Captcha Response Code: {captcha_code}")

        # insert captcha into g-recaptcha-response textarea and submit form
        form = self.driver.find_element(By.NAME, 'captcha_form')
        textarea = form.find_element(By.NAME, 'h-captcha-response')
        self.driver.execute_script("arguments[0].value = arguments[1];", textarea, captcha_code)
        form.submit()

    def get_captcha_response_code(self, url) -> str:
        self.current_captcha_retries += 1
        print(f'Captcha solving try #{self.current_captcha_retries}')

        try:
            print(f"Started solving catpcha for {url} ({SITE_KEY})\nPlease wait.")
            result = self.solver.hcaptcha(sitekey=SITE_KEY, url=url)
        except twocaptcha.api.ApiException as e:
            print(str(e))
            if self.current_captcha_retries >= self.max_captcha_retries:
                raise ValueError(f"Max {self.current_captcha_retries} Captcha Retries reached")

            return self.get_captcha_response_code(url)

        self.current_captcha_retries = 0
        return result['code']


if __name__ == '__main__':
    SolverPOC().run(query='J.G. Wentworth Originations, LLC')
