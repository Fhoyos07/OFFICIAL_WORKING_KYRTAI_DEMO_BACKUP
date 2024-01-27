# KYRT - iapps.courts.state.ny.us

## Summary:
Python/Scrapy script with input from CSV and output to CSV and download PDF files.

## Executables:

## python3 RUN.py will run both Step 1 and Step 2. Alternativly, you can run Step 1, then run Step 2 manually. For full automation, just run python3 RUN.py

### Step 1: Find all cases and documents
`python3 step1_csv.py`

#### Input:
- `/files/input.csv` - list of companies under column "Competitor / Fictitious LLC Name"

#### Output: 
- `/files/kyrt_ny_companies.csv` - stats of company scraping (how many cases, when was the latest)
- `/files/kyrt_ny_cases.csv` - cases results
- `/files/kyrt_ny_documents.csv` - documents results


### Step 2: Download all PDFs
`python3 step2_pdf.py`

#### Input:
- `/files/kyrt_ny_documents.csv` - list of URLs, under columns Document URL and Status Document URL (once per case)

#### Output: 
- `/files/pdfs` - pdf dir with files grouped by Case Number

## Settings:
- `/scrapy_app/settings.py` - scraping settings. Main:
  * `DAYS_BACK` (default 10) - min date to scrape cases
  * `MAX_CAPTCHA_RETRIES` (default 10) - max sequential fails to give up with 2captcha
  * `TWO_CAPTCHA_API_KEY`
  * `USE_CACHE` (default False) - if True, tries to load the session from the previous session on start. may be unstable.

  
---
### Technical details:
### Stack:
* Python 3.8+
* Scrapy 2.0+
* requests
* 2captcha-python

### Python requirements:
`/etc/requirements.txt`

Installation of requirements:  
`pip3 install -r etc/requirements.txt`

### Debug logs:
- `/_etc/logs/debug.log`

### 
settings.py
MAX_COMPANIES = 80
/
MAX_COMPANIES = None # crawl all
