import twocaptcha.api
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from parsel import Selector

TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
SITE_KEY = '41b778e7-8f20-45cc-a804-1f1ebb45c579'

class SolverPOC:
    def __init__(self):
        self.solver = TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, 3

        # selenium options
        options = Options()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--verbose")
        # options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)

    def run(self):
        # open search page
        self.driver.get(f'https://2captcha.com/demo/hcaptcha')

        print('Start solving captcha?')
        # solve captcha using 2captcha
        self.solve_captcha()

        input('Continue?')

    def solve_captcha(self) -> None:
        captcha_code = self.get_captcha_response_code(url=self.driver.current_url)
        print(f"Captcha Response Code: {captcha_code}")

        # insert captcha into g-recaptcha-response textarea and submit form
        form = self.driver.find_element(By.XPATH, '//form[@novalidate]')
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
    SolverPOC().run()
