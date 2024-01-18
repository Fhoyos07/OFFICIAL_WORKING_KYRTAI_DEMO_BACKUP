import os
from scrapy.crawler import Crawler
from scrapy.spiders import Spider
from scrapy.exporters import CsvItemExporter
from typing import TextIO


class LoggingPipeline:
    def process_item(self, item, spider):
        spider.logger.info(item)
        return item


class CsvBasePipeline:
    """
    Base class for both versions of CSV spider.
    Version 1 (CsvPipeline): writing each item immediately during scraping
    Version 2 (CsvOnClosePipeline): collecting all items and writing them at once on spider finish
    """
    def __init__(self, spider: Spider):
        self.spider_name = spider.name
        self.csv_dir = spider.settings.get('CSV_DIR')
        if not self.csv_dir:
            raise ValueError('CSV_DIR not specified in settings')
        os.makedirs(self.csv_dir, exist_ok=True)

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(spider=crawler.spider)

    # helper methods
    def open_file(self, file_name: str = None, fields_to_export: list[str] = None) -> (str, TextIO, CsvItemExporter):
        """Open CSV file for exporting"""
        file_name = file_name or f'{self.spider_name}.csv'
        csv_path = os.path.join(self.csv_dir, file_name)

        csv_file = open(csv_path, mode='w+b')
        exporter = CsvItemExporter(csv_file, encoding='utf-8-sig', fields_to_export=fields_to_export)
        return csv_path, csv_file, exporter


class CsvOnClosePipeline(CsvBasePipeline):
    """
    Pipeline for writing to CSV file, collecting all items and writing them at once on spider finish
    """
    items = None

    def open_spider(self, spider):
        self.items = []

    def process_item(self, item, spider):
        self.items.append(item)
        return item

    def close_spider(self, spider):
        self.export_items(self.items)

    # helper methods
    def export_items(self, items: list[dict], file_name: str = None) -> str:
        fields_to_export = self.collect_fields(items)
        csv_path, csv_file, exporter = self.open_file(file_name=file_name, fields_to_export=fields_to_export)
        for item in items:
            exporter.export_item(item)
        csv_file.close()
        return csv_path

    @staticmethod
    def collect_fields(items: list[dict]) -> list[str]:
        fields = []  # list of all fields (used as csv header)
        for item in items:
            for field in item:
                if field not in fields:
                    fields.append(field)
        return fields


class CsvPipeline(CsvBasePipeline):
    """
    Pipeline for writing to CSV file, each item immediately during scraping
    """
    csv_file = None
    exporter = None

    def open_spider(self, spider):
        self.csv_file, self.exporter = self.open_file()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.csv_file.close()


class S3Pipeline:
    """
    Required settings:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_S3_BUCKET_NAME
    Optional settings:
    - CSV_DIR - enable upload by file_name using upload_csv method
    """
    def __init__(self, spider: Spider):
        import boto3
        session = boto3.session.Session()
        self.client = session.client("s3",
                                     aws_access_key_id=spider.settings['AWS_ACCESS_KEY_ID'],
                                     aws_secret_access_key=spider.settings['AWS_SECRET_ACCESS_KEY'])
        self.settings = spider.settings
        # self.s3_bucket_name = spider.settings['AWS_S3_BUCKET_NAME']

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(spider=crawler.spider)

    def upload_file(self, file_path: str, s3_folder_name: str, public: bool = False):
        self.client.upload_file(Bucket=self.settings['AWS_S3_BUCKET_NAME'],
                                Filename=file_path,
                                Key=f"{s3_folder_name}/{os.path.basename(file_path)}",
                                ExtraArgs={'ACL': 'public-read'} if public else None)

    def upload_csv(self, file_name: str, s3_folder_name: str, **kwargs):
        file_path = os.path.join(self.settings['CSV_DIR'], file_name)
        self.upload_file(file_path=file_path, s3_folder_name=s3_folder_name, **kwargs)
