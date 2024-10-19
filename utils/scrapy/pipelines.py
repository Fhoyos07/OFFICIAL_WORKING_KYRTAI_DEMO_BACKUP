import os
import json
import csv
from scrapy.crawler import Crawler
from scrapy.spiders import Spider
from dataclasses import dataclass
from itemadapter import ItemAdapter
from typing import IO
from pathlib import Path


class LoggingPipeline:
    def process_item(self, item, spider):
        item = ItemAdapter(item)    # convert to dict-like object
        spider.logger.info(json.dumps(item, indent=2))
        return item


class BasePipeline:
    """Make spider params available"""
    def __init__(self, spider: Spider):
        # assign spider params
        self.spider = spider
        self.settings = spider.settings
        self.logger = spider.logger

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(spider=crawler.spider)


class CsvPipeline(BasePipeline):
    """
    Pipeline for writing to CSV file during spider crawl.
    Support writing multiple item types simultaneously.
    """
    def __init__(self, spider: Spider):
        super().__init__(spider)
        if not self.settings.get('CSV_DIR'):
            raise ValueError('CSV_DIR not specified in settings')

        self.csv_dir: Path = Path(self.settings['CSV_DIR'])
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Using {self.csv_dir} as dir for CSV export")

        self.csv_writer_by_type: dict[str, CsvWriterWrapper] = {}

    def process_item(self, item, spider):
        item = ItemAdapter(item)    # convert to dict-like object

        # use item._type to group items, or just spider.name
        item_type = item.pop('_type', self.spider.name)

        # get CSV file writer for item type, or start a new one
        csv_writer: CsvWriterWrapper = self.csv_writer_by_type.get(item_type)
        if csv_writer is None:
            csv_writer = self._open_csv_writer(csv_name=item_type, fieldnames=list(item.keys()), write_header=True)
            self.csv_writer_by_type[item_type] = csv_writer

        # write item to CSV
        csv_writer.writerow(item)
        return item

    def close_spider(self, spider):
        for csv_writer in self.csv_writer_by_type.values():
            csv_writer.close()

    def _open_csv_writer(self, csv_name: str, fieldnames: list[str], write_header: bool = False) -> 'CsvWriterWrapper':
        csv_path = self.csv_dir / f'{csv_name.lower()}.csv'
        self.logger.info(f"Opening CSV writer at {csv_path} with fieldnames:\n {','.join(fieldnames)}")
        csv_writer = CsvWriterWrapper(csv_path=csv_path, fieldnames=fieldnames)
        if write_header:
            csv_writer.writeheader()
        return csv_writer


class CsvOnClosePipeline(CsvPipeline):
    """
    Pipeline for writing to CSV file, collecting all items and writing them at once on spider finish.
    Support writing only 1 writing type.
    """
    def __init__(self, spider: Spider):
        super().__init__(spider)
        self.items = []

    def process_item(self, item, spider):
        item = ItemAdapter(item)    # convert to dict-like object
        self.items.append(item)
        return item

    def close_spider(self, spider):
        fields_to_export = self.collect_fields(self.items)
        csv_writer = self._open_csv_writer(csv_name=spider.name,
                                           fieldnames=fields_to_export,
                                           write_header=True)
        csv_writer.writerows(self.items)
        csv_writer.close()

    @staticmethod
    def collect_fields(items: list[dict]) -> list[str]:
        """Get list of all fields from all items (used as csv header)"""
        fields = []
        for item in items:
            for field in item:
                if field not in fields:
                    fields.append(field)
        return fields


@dataclass
class CsvWriterWrapper:
    _writer: csv.DictWriter
    _file: IO

    def __init__(self, csv_path: Path, fieldnames: list[str], encoding: str = 'utf-8', override: bool = True):
        if override is True and csv_path.exists():
            csv_path.unlink()  # delete existing file

        self._encoding = encoding
        self._header_written = csv_path.exists()

        self._file = open(csv_path, mode='a', encoding=self._encoding, newline='')
        self._writer = csv.DictWriter(self._file, fieldnames=fieldnames)

    def writeheader(self):
        if not self._header_written:
            self._writer.writeheader()
            self._header_written = True

            # Switch to append mode after writing header
            self._file.close()
            self._file = open(self._file.name, mode='a', encoding=self._encoding, newline='')
            self._writer = csv.DictWriter(self._file, self._writer.fieldnames)

    def writerow(self, rowdict):
        self._writer.writerow(rowdict)
        self._file.flush()  # make file changes visible immediately

    def writerows(self, rowdicts):
        self._writer.writerows(rowdicts)
        self._file.flush()  # make file changes visible immediately

    # file methods
    def close(self):
        self._file.close()


class S3Pipeline(BasePipeline):
    """
    Required settings:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_S3_BUCKET_NAME
    Optional settings:
    - CSV_DIR - enable upload by file_name using upload_csv method
    """
    def __init__(self, spider: Spider):
        super().__init__(spider)

        try:
            import boto3
        except ImportError as e:
            raise ImportError("boto3 is not installed. Use `pip3 install boto3`") from e

        session = boto3.session.Session()
        if not self.settings.get('CSV_DIR'):
            raise ValueError('CSV_DIR not specified in settings')
        self.csv_dir: Path = Path(self.settings['CSV_DIR'])

        self.client = session.client("s3",
                                     aws_access_key_id=self.settings['AWS_ACCESS_KEY_ID'],
                                     aws_secret_access_key=self.settings['AWS_SECRET_ACCESS_KEY'])

    def upload_file(self, file_path: str, s3_folder_name: str, public: bool = False):
        self.client.upload_file(Bucket=self.settings['AWS_S3_BUCKET_NAME'],
                                Filename=file_path,
                                Key=f"{s3_folder_name}/{os.path.basename(file_path)}",
                                ExtraArgs={'ACL': 'public-read'} if public else None)

    def upload_csv(self, file_name: str, s3_folder_name: str, **kwargs):
        file_path = os.path.join(self.settings['CSV_DIR'], file_name)
        self.upload_file(file_path=file_path, s3_folder_name=s3_folder_name, **kwargs)
