# KYRT
### Spiders for:  
- iapps.courts.state.ny.us
- civilinquiry.jud.ct.gov (CT)

## Summary:
Python/Scrapy scripts with input from CSV and output to CSV and download PDF files.
All scripts share the same flow:
- Read input CSV.
- Find cases for all companies.
- Export company statistics (cases found) to `companies.csv` - overriding existing file/
- Export cases to `cases.csv` - appending to end of file.
- Export documents metadata (url, name) to `documents.csv` - appending to end of file.
- Cases and documents are added only once, later crawlings skip existing items from CSV.
- Download document pdfs to folder.

## Executables:
#### NY Spider
- `python3 RUN_NY.py`
- Input: `/files/input.csv`
- Output: `/files/NY/`

## python3 RUN_CT.py
- `python3 RUN_CT.py`
- Input: `/files/input.csv`
- Output: `/files/CT/`

## python3 RUN_NY_proceedings.py
- `python3 RUN_NY_proceedings.py`
- Input: `/files/input_ny_proceedings.csv`
- Output: `/files/NY_proceedings/`

## Settings:
- `/scrapy_app/settings.py` - scraping settings. Main:
  * `DAYS_BACK` (default 14) - min date to scrape cases
  * `MAX_CAPTCHA_RETRIES` (default 20) - max sequential fails to give up with 2captcha
  * `TWO_CAPTCHA_API_KEY`

  
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
