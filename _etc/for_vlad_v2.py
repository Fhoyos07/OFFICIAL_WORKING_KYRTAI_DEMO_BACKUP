import os
import csv
import time
import datetime
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Logger
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select  # <-- Add this import for Select
from twocaptcha import TwoCaptcha
import twocaptcha
from bs4 import BeautifulSoup


# Please note, the code will cick on the "Name" tab on the search to search by Name.
# When trying to access that URL directly i.e. https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name,
# it doesn't seem to work properly so this was a way to accomplish it
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
# PROXY_SERVICE = API_KEY - # Figure out something for proxy IP stuff here from a giant pool of IP's
PDF_DOWNLOAD_DELAY = 2  # seconds
DAYS_BACK = 10          # Look for cases from the last 60 days
TWO_CAPTCHA_API_KEY = '3408dd86d795e88a4c8e8e2860b25e94'
MAX_CAPTCHA_RETRIES = 7


def setup_logging() -> Logger:
    LOGS_DIRECTORY = "logs"  # Directory to store logs
    # Ensure the logs directory exists
    if not os.path.exists(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)

    # Configure logging to also output to a file with a unique name
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Ensuring that INFO and above level messages are captured
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File Handler for logs
    log_filename = os.path.join(LOGS_DIRECTORY, f"NYSCaseScraper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


class Crawler:
    BASE_URL = "https://iapps.courts.state.ny.us/nyscef"

    def __init__(self):
        self.logger = setup_logging()

        options = Options()
        options.add_argument("-headless")
        self.driver = webdriver.Firefox(options=options)

        self.solver = TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, MAX_CAPTCHA_RETRIES

    @staticmethod
    def get_queries() -> list[str]:
        return ['J.G. Wentworth Originations, LLC']

    def main(self):
        for name in self.get_queries():
            self.logger.info(f"Starting the scraper for {name}.")
            self.scrape_data(name)  # Pass the driver to scrape data
            self.process_cases()  # Use the same driver to process each case

        self.logger.info("The script has completed running successfully, please check your PDF and Log folders for more information.")

    def scrape_data(self, business_name):
        wait = WebDriverWait(self.driver, 30)
        data = []
        date_cutoff = datetime.datetime.now() - datetime.timedelta(days=DAYS_BACK)

        self.driver.get(f"{self.BASE_URL}/CaseSearch?TAB=name")
        self.logger.info("Accessed the NYSCef Case Search page.")
        input_field = wait.until(EC.visibility_of_element_located((By.NAME, 'txtBusinessOrgName')))
        input_field.send_keys(business_name)
        self.logger.info(f"Entered business name: {business_name}")

        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.BTN_Green.g-recaptcha')))
        search_button.click()
        self.logger.info("Clicked the search button.")

        self.solve_captcha()

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'NewSearchResults')))
        self.logger.info("Search results loaded.")
        time.sleep(10)

        sort_dropdown = Select(self.driver.find_element(By.ID, "selSortBy"))
        sort_dropdown.select_by_value("FilingDateDesc")
        sort_button = self.driver.find_element(By.NAME, "btnSort")
        sort_button.click()
        time.sleep(5)
        self.logger.info("Sorted the results by filing date in descending order.")

        stop_processing = False
        while not stop_processing:
            stop_processing = not self.extract_and_save_data(data, date_cutoff)
            try:
                next_page_button = self.driver.find_element(By.XPATH, "//a[contains(text(), '>>')]")
                if next_page_button:
                    next_page_button.click()
                    time.sleep(5)
                    self.logger.info("Navigated to the next page of results.")
                else:
                    break
            except Exception as e:
                self.logger.error(f"No more pages or unable to navigate further. Error: {e}")
                break

        self.save_to_csv(data)

    # def solve_captcha(self):
    #     input("CAPTCHA check: Please manually check the browser for a CAPTCHA. Solve it (if present - otherwise code will proceed automatically), then press Enter here to continue...")

    def solve_captcha(self) -> None:
        if not self.driver.find_elements(By.NAME, 'captcha_form'):
            self.logger.info(f"Captcha not found")
            return

        captcha_code = self.get_captcha_response_code(url=self.driver.current_url)
        self.logger.info(f"Captcha Response Code: {captcha_code}")

        # insert captcha into g-recaptcha-response textarea and submit form
        form = self.driver.find_element(By.NAME, 'captcha_form')
        textarea = form.find_element(By.NAME, 'g-recaptcha-response')
        self.driver.execute_script("arguments[0].value = arguments[1];", textarea, captcha_code)
        form.submit()

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

    def extract_and_save_data(self, data, date_cutoff):
        rows = self.driver.find_elements(By.XPATH, "//table[@class='NewSearchResults']/tbody/tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                date_str = cells[0].text.split('\n')[1]
                date_obj = datetime.datetime.strptime(date_str, '%m/%d/%Y')
                if date_obj >= date_cutoff:
                    case_url = cells[0].find_element(By.TAG_NAME, "a").get_attribute("href")
                    case_info = {
                        "Case Number": cells[0].text,
                        "eFiling Status": cells[1].text,
                        "Caption": cells[2].text,
                        "Court & Case Type": cells[3].text,
                        "URL": case_url
                    }
                    data.append(case_info)
                    self.logger.info(f"Added case: {case_info}")
                else:
                    self.logger.info(f"Date cutoff reached. Stopping data extraction.")
                    return False
        return True

    def save_to_csv(self, data):
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
        with open('pdfs/scraped_data.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=data[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(data)
        self.logger.info(f"Saved scraped data to 'pdfs/scraped_data.csv'.")

    def process_cases(self):
        with open('pdfs/scraped_data.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                case_number = row['Case Number'].split('\n')[0].replace('/', '_')
                url = row['URL']
                self.scrape_and_download_case_pdfs(case_url=url, directory=case_number)

    def scrape_and_download_case_pdfs(self, case_url, directory):
        try:
            self.driver.get(case_url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
            page_source = self.driver.page_source

            # find pdf links
            soup = BeautifulSoup(page_source, 'html.parser')
            links = soup.find_all('a', href=True)
            pdf_links =  [link['href'] for link in links if 'ConfirmationNotice?docId=' in link['href'] or 'ViewDocument?docIndex=' in link['href']]

            for pdf_link in pdf_links:
                self.download_pdf(f"{self.BASE_URL}/{pdf_link}", directory)
        except Exception as e:
            self.logger.error(f"Error processing case {case_url}: {e}")

    def download_pdf(self, url, target_directory):
        headers = {'User-Agent': USER_AGENT}
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

    def __del__(self):
        self.driver.quit()


if __name__ == "__main__":
    Crawler().main()
