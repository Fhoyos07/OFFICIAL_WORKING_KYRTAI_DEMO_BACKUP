from functools import wraps
from scrapy.spiders import Spider
from scrapy.http import Response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.python.failure import Failure

import pathlib
import os
import json
import logging

from typing import Callable


# todo: refactor
def log_response(f: Callable) -> Callable:
    """
    Spider decorator to log page name
    """
    @wraps(f)
    def wrap(self: Spider, response_or_failure: Response | HttpError | Failure, **kwargs) -> Callable:
        if not isinstance(response_or_failure, Failure):    # for successful requests
            page_title = f.__name__.replace('parse_', '').upper()
            debug_kwargs = {'url': response_or_failure.url}

        elif response_or_failure.check(HttpError):          # for HTTP errors
            page_title = 'HTTP ERROR'
            response = response_or_failure.value.response
            debug_kwargs = {'url': response.url, 'status': response.status}

        else:   # for network errors
            page_title = 'NETWORK ERROR'
            request = response_or_failure.request
            debug_kwargs = {'url': request.url, 'error': repr(response_or_failure)}

        debug_string = ', '.join(f'{k}: {v}' for k, v in debug_kwargs.items())
        self.logger.info(f'Opened {page_title} page ({debug_string})')

        return f(self, response_or_failure, **kwargs)
    return wrap


def save_response(f: Callable) -> Callable:
    """
    Spider decorator to save response to file
    Required Scrapy settings:
    - PROJECT_DIR
    Optional Scrapy settings:
    - HTML_DIR - main directory to store htmls (have subfolders per each spider)
    """
    @wraps(f)
    def wrap(self: Spider, response_or_failure: Response | HttpError | Failure, **kwargs) -> Callable:
        HTML_DIR, PROJECT_DIR = self.settings.get('HTML_DIR'), self.settings.get('PROJECT_DIR')
        if not PROJECT_DIR:
            raise AttributeError("PROJECT_DIR attribute wasn't found in settings.py")

        HTML_DIR = HTML_DIR or os.path.join(PROJECT_DIR, 'etc', 'html')
        html_dir_for_spider = os.path.join(HTML_DIR, self.name)

        pathlib.Path(html_dir_for_spider).mkdir(parents=True, exist_ok=True)

        page_title = f.__name__.replace('parse_', '')

        if not isinstance(response_or_failure, Failure) or response_or_failure.check(HttpError):
            if isinstance(response_or_failure, Failure):
                response = response_or_failure.value.response
            else:
                response = response_or_failure

            try:
                assert 'Content-Type' in response.headers
                content_type = response.headers.get('Content-Type').decode('utf-8')
                assert 'json' in content_type.lower()

                file_name = f'{page_title}.json'
                file_content = json.dumps(json.loads(response.text), indent=2, ensure_ascii=False)

            except (AssertionError, TypeError, ValueError, AttributeError, json.decoder.JSONDecodeError) as e:
                file_name = f'{page_title}.html'
                file_content = response.text

            file_path = os.path.join(html_dir_for_spider, file_name)
            with open(file_path, mode='w', encoding='utf-8') as fp:
                fp.write(file_content)

            self.logger.info(f'Saved response to {pathlib.Path(file_path).as_uri()}')

        return f(self, response_or_failure, **kwargs)
    return wrap


def log_method(f):
    """logging methods and their arguments for scrapy spiders"""
    @wraps(f)
    def wrap(self, *args, **kwargs):
        logging_message = f'Call function {f.__name__.upper()}.'
        if args:
            logging_message += f" Args: {', '.join(str(a) for a in args)}."
        if kwargs:
            logging_message += f' Kwargs: {kwargs}.'
        self.logger.info(logging_message)

        return f(self, *args, **kwargs)
    return wrap


def measure_time(f):
    """decorator to measure time """
    def timed(*args, **kwargs):
        from datetime import datetime
        ts = datetime.now()
        logging.info(f"Function {f.__name__.upper()} started at {ts.isoformat(' ', 'seconds')}")

        result = f(*args, **kwargs)

        te = datetime.now()
        logging.info(f"Function {f.__name__.upper()} ended at {te.isoformat(' ', 'seconds')}")
        logging.info(f'Duration: {te-ts}')

        return result
    return timed


def update_progress(f):
    """
    Scrapy decorator to update progress bar
    """
    @wraps(f)
    def wrap(self, *args, **kwargs):
        from tqdm import tqdm
        if getattr(self, 'progress_bar', None) is None:
            self.progress_bar = tqdm()

        self.progress_bar.update()
        return f(self, *args, **kwargs)
    return wrap


