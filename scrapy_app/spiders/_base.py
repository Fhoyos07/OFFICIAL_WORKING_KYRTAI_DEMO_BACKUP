from abc import ABC, abstractmethod
from scrapy import Spider
from scrapy.http import Request, FormRequest, TextResponse
from datetime import date, datetime, timedelta
from http.cookies import SimpleCookie
from tqdm import tqdm
import twocaptcha
import os

from ..utils.scrapy.decorators import log_response, save_response, log_method
from ..utils.file import load_json, save_json, load_csv
from ..utils.scrapy.url import parse_url_params
from ..settings import (INPUT_CSV_PATH, DAYS_BACK, MAX_COMPANIES, TWO_CAPTCHA_API_KEY, MAX_CAPTCHA_RETRIES)


class KyrtBaseCaseSpider(ABC, Spider):
    def __init__(self):
        # parse input CSV
        companies = [row['Competitor / Fictitious LLC Name'] for row in load_csv(INPUT_CSV_PATH)]
        companies = [c.strip().upper().replace(', LLC', ' LLC') for c in companies]
        if MAX_COMPANIES:
            companies = companies[:MAX_COMPANIES]
            self.logger.info(f"Cut companies to only {MAX_COMPANIES} first")

        self.QUERIES = sorted(list(set(c for c in companies if c)))
        self.logger.info(f"After deduplication: {len(self.QUERIES)} companies")

        # set up progress bar
        self.logger.info(f"len(self.QUERIES): {len(self.QUERIES)}")
        self.progress_bar = tqdm(total=len(self.QUERIES))

        # min case date to crawl
        self.MIN_DATE = date.today() - timedelta(days=DAYS_BACK)

        # captcha settings
        self.solver = twocaptcha.TwoCaptcha(apiKey=TWO_CAPTCHA_API_KEY)
        self.current_captcha_retries, self.max_captcha_retries = 0, MAX_CAPTCHA_RETRIES


        # collect existing ids to avoid scraping same case twice
        self.existing_case_ids = set()
        super().__init__()
