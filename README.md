# KYRT
TODO:
1. connect
2. setup postgres
3. setup git
4. setup django
5. create models for scrapy apps.


### Spiders for:  
- iapps.courts.state.ny.us
- civilinquiry.jud.ct.gov (CT)

## Summary:
Python/Scrapy scripts with input from CSV and output to CSV and download PDF files.
All scripts share the same flow:
- Read input CSV.
- Find cases for all companies.
- Export company statistics (cases found) to `companies.csv` - overriding existing file.
- Export cases to `cases.csv` - appending to end of file.
- Export documents metadata (url, name) to `documents.csv` - appending to end of file.
- Cases and documents are added only once, later crawlings skip existing items from CSV.
- Download document pdfs to folder.

## Executables:
#### Main Script
- `python3 RUN.py` - provides list of spiders to choose

#### NY Spider
- `python3 RUN.py NY`
- Input: `/files/input.csv`
- Output: `/files/NY/`

#### CT Spider
- `python3 RUN.py CT`
- Input: `/files/input.csv`
- Output: `/files/CT/`

#### NY Proceedings Spider
- `python3 RUN.py NY_proceedings`
- Input: `/files/input_ny_proceedings.csv`
- Output: `/files/NY_proceedings/`

## Settings:
- `/scraping_service/settings.py` - scraping settings. Main:
  * `DAYS_BACK` (default 14) - min date to scrape cases
  * `MAX_CAPTCHA_RETRIES` (default 20) - max sequential fails to give up with 2captcha
  * `TWO_CAPTCHA_API_KEY`


## Flows:
24STCP00074
https://www.lacourt.org/casesummary/ui/index.aspx?casetype=civil
  
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


### re-deploy server
killall gunicorn && cd ~/KYRT && . .venv/bin/activate && nohup gunicorn --workers 3 config.wsgi:application --bind localhost:8000 > gunicorn.log 2>&1 &
