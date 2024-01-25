import os
import csv
import requests
import time
from pathlib import Path
from scrapy.crawler import Crawler
from scrapy.spiders import Spider
from scrapy.exporters import CsvItemExporter
from typing import TextIO


class BasePipeline:
    """Make spider params available"""
    def __init__(self, spider: Spider):
        # assign spider params
        self.spider_name = spider.name
        self.settings = spider.settings
        self.logger = spider.logger

        self.files_dir = self.settings.get('FILES_DIR')
        if not self.files_dir:
            raise ValueError('FILES_DIR not specified in settings')
        os.makedirs(self.files_dir, exist_ok=True)

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(spider=crawler.spider)


class CsvPipeline(BasePipeline):
    """
    Pipeline for writing to CSV file, collecting all items and writing them at once on spider finish
    """
    def __init__(self, spider: Spider):
        # lists to store scraped items
        self.dict_writer_by_type: dict[str, csv.DictWriter] = {}
        super().__init__(spider)

    def process_item(self, item, spider):
        item_type = item.pop('_item_type')

        # get CSV file writer for item type, or start a new one
        csv_writer = self.dict_writer_by_type.get(item_type)
        if not csv_writer:
            csv_writer = self.init_dict_writer(item_type, fieldnames=list(item.keys()))
            self.dict_writer_by_type[item_type] = csv_writer

        # write item to CSV
        csv_writer.writerow(item)
        return item

    def init_dict_writer(self, item_type: str, fieldnames: list[str]):
        csv_path = os.path.join(self.files_dir, f'{item_type.lower()}.csv')

        csv_file = open(csv_path, mode='w', encoding='utf-8-sig')
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        return csv_writer


class DocumentSavePipeline(BasePipeline):
    def process_item(self, item, spider):
        # generate pdf path
        pdf_path = Path(self.files_dir) / 'pdfs' / item['relative_file_path']
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # save to file
        with open(pdf_path, 'wb') as file:
            file.write(item['body'])
        self.logger.debug(f"Wrote to {pdf_path}")
