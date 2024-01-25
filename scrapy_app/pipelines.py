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
        self.items_by_type: dict[str, list[dict]] = {}
        super().__init__(spider)

    def process_item(self, item, spider):
        item_type = item.pop('_item_type')
        self.items_by_type.setdefault(item_type, []).append(item)
        return item

    def close_spider(self, spider):
        for item_type, items in self.items_by_type.items():
            self.export_items_to_csv(items, csv_name=f'{item_type.lower()}.csv')

    def export_items_to_csv(self, items: list[dict], csv_name: str):
        # get CSV path and collect CSV fields
        csv_path = os.path.join(self.files_dir, csv_name)

        if not items:
            self.logger.info(f"No items to export to {csv_name}. Skipping.")
            if os.path.exists(csv_path):
                os.remove(csv_path)
            return

        fields_to_export = self.collect_fields(items)

        # export items
        with open(csv_path, mode='w', encoding='utf-8-sig') as f:
            csv_writer = csv.DictWriter(f, fieldnames=fields_to_export)
            csv_writer.writeheader()
            csv_writer.writerows(items)
        self.logger.info(f"Exported {len(items)} to {csv_path}")

    @staticmethod
    def collect_fields(items: list[dict]) -> list[str]:
        fields = []  # list of all fields (used as csv header)
        for item in items:
            for field in item:
                if field not in fields:
                    fields.append(field)
        return fields


class DocumentSavePipeline(BasePipeline):
    def process_item(self, item, spider):
        # generate pdf path
        pdf_path = Path(self.files_dir) / 'pdfs' / item['relative_file_path']
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # save to file
        with open(pdf_path, 'wb') as file:
            file.write(item['body'])
        self.logger.debug(f"Wrote to {pdf_path}")
