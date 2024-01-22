# Web crawling project for iapps.courts.state.ny.us

## Summary:
Python/Scrapy script with input from CSV and output to CSV and download PDF files.

## Executables:
`python3 RUN.py`

### Input:
- `/input.csv` - list of companies under column "Competitor / Fictitious LLC Name"

### Output: 
- `/results/courts_ny_companies.csv` - stats of company scraping (how many cases, when was the latest)
- `/results/courts_ny_cases.csv` - cases results
- `/results/courts_ny_documents.csv` - documents results
- `/results/pdfs`

### Settings:
- `/scrapy_app/settings.py` - scraping settings (especially, `DAYS_BACK`, `MAX_CAPTCHA_RETRIES`, `TWO_CAPTCHA_API_KEY`)

### Technical details:
- 

---
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
- `/_etc/logs/error.log`

---

### Client:
Anthony

### Developer:
Vlad Tyazhov  
`tva1992@gmail.com`