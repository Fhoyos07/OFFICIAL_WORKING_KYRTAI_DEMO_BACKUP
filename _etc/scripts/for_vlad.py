import os
import csv
import time
import datetime
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select  # <-- Add this import for Select
from bs4 import BeautifulSoup

# Configure logging to also output to a file with a unique name
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(f"NYSCaseScraper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                        logging.StreamHandler()
                    ])

# Constants
BASE_URL = "https://iapps.courts.state.ny.us/nyscef/" # Please note, the code will cick on the "Name" tab on the search to search by Name. When trying to 
                                                      # access that URL directly i.e. https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name it doesn't
                                                      # seem to work properly so this was a way to accomplish it

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3' #Eventually auto rotate/randomize this
# PROXY_SERVICE = API_KEY - # Figure out something for proxy IP stuff here from a giant pool of IP's
PDF_DOWNLOAD_DELAY = 2  # seconds
DAYS_BACK = 10  # Look for cases from the last 60 days
LOGS_DIRECTORY = "logs" # Directory to store logs

# Ensure the logs directory exists
if not os.path.exists(LOGS_DIRECTORY):
    os.makedirs(LOGS_DIRECTORY)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Ensuring that INFO and above level messages are captured
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


# File Handler for logs
log_filename = os.path.join(LOGS_DIRECTORY, f"NYSCaseScraper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# File Handler for logs
log_filename = os.path.join(LOGS_DIRECTORY, f"NYSCaseScraper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def check_for_captcha(driver):
    input("CAPTCHA check: Please manually check the browser for a CAPTCHA. Solve it (if present - otherwise code will proceed automatically), then press Enter here to continue...")

def download_pdf(url, target_directory):
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
        logging.info(f"Downloaded {file_name} to {target_subdir}")
        time.sleep(PDF_DOWNLOAD_DELAY)
    else:
        logging.error(f"Failed to download {url}. Status code: {response.status_code}")

def scrape_data(business_name, driver):
    wait = WebDriverWait(driver, 30)
    data = []
    date_cutoff = datetime.datetime.now() - datetime.timedelta(days=DAYS_BACK)

    driver.get(BASE_URL + 'CaseSearch?TAB=name')
    logging.info("Accessed the NYSCef Case Search page.")
    input_field = wait.until(EC.visibility_of_element_located((By.NAME, 'txtBusinessOrgName')))
    input_field.send_keys(business_name)
    logging.info(f"Entered business name: {business_name}")

    search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.BTN_Green.g-recaptcha')))
    search_button.click()
    logging.info("Clicked the search button.")

    check_for_captcha(driver)

    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'NewSearchResults')))
    logging.info("Search results loaded.")
    time.sleep(10)

    sort_dropdown = Select(driver.find_element(By.ID, "selSortBy"))
    sort_dropdown.select_by_value("FilingDateDesc")
    sort_button = driver.find_element(By.NAME, "btnSort")
    sort_button.click()
    time.sleep(5)
    logging.info("Sorted the results by filing date in descending order.")

    stop_processing = False
    while not stop_processing:
        stop_processing = not extract_and_save_data(driver, data, date_cutoff)
        try:
            next_page_button = driver.find_element(By.XPATH, "//a[contains(text(), '>>')]")
            if next_page_button:
                next_page_button.click()
                time.sleep(5)
                logging.info("Navigated to the next page of results.")
            else:
                break
        except Exception as e:
            logging.error(f"No more pages or unable to navigate further. Error: {e}")
            break

    save_to_csv(data)

def extract_and_save_data(driver, data, date_cutoff):
    rows = driver.find_elements(By.XPATH, "//table[@class='NewSearchResults']/tbody/tr")
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
                logging.info(f"Added case: {case_info}")
            else:
                logging.info(f"Date cutoff reached. Stopping data extraction.")
                return False
    return True

def save_to_csv(data):
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')
    with open('pdfs/scraped_data.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=data[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(data)
    logging.info(f"Saved scraped data to 'pdfs/scraped_data.csv'.")

def process_cases(driver):
    with open('pdfs/scraped_data.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            case_number = row['Case Number'].split('\n')[0].replace('/', '_')
            url = row['URL']
            directory = case_number
            scrape_and_download_case_pdfs(driver, url, directory)

def scrape_and_download_case_pdfs(driver, case_url, directory):
    try:
        driver.get(case_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
        page_source = driver.page_source
        pdf_links = find_pdf_links(page_source)
        for pdf_link in pdf_links:
            download_pdf(BASE_URL + pdf_link, directory)
    except Exception as e:
        logging.error(f"Error processing case {case_url}: {e}")

def find_pdf_links(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    links = soup.find_all('a', href=True)
    return [link['href'] for link in links if 'ConfirmationNotice?docId=' in link['href'] or 'ViewDocument?docIndex=' in link['href']]

def main():
    options = Options()
    options.headless = True  # Set to True if you don't need the browser window
    driver = webdriver.Firefox(options=options)
    try:
        logger.info("Starting the scraper.")
        scrape_data('J.G. Wentworth Originations, LLC', driver)  # Pass the driver to scrape data
        process_cases(driver)  # Use the same driver to process each case
        logger.info("The script has completed running successfully, please check your PDF and Log folders for more information.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()