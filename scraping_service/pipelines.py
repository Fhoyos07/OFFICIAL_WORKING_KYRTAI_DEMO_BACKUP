from itemadapter import ItemAdapter
from scrapy.crawler import Crawler
from pathlib import Path
from scrapy import Spider
import json

from utils.scrapy.pipelines import CsvWriterWrapper
from apps.web.models import Case, Document
from .items import CaseItem, CaseItemCT, CaseItemNY, DocumentItem, DocumentItemCT


class LoggingPipeline:
    def process_item(self, item, spider):
        item_dict = ItemAdapter(item).asdict()
        spider.logger.info(json.dumps(item_dict, indent=2))
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


class DocumentSavePipeline(BasePipeline):
    def __init__(self, spider: Spider):
        super().__init__(spider)
        self.pdf_dir = Path(self.settings['FILES_DIR']) / spider.state_code / 'pdfs'

    def process_item(self, item: dict, spider: Spider):
        # generate pdf path
        pdf_path = self.pdf_dir / item['relative_file_path']
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # save to file
        with open(pdf_path, 'wb') as file:
            file.write(item['body'])
        self.logger.debug(f"Wrote to {pdf_path}")


class CsvPipeline(BasePipeline):
    """
    Pipeline for writing to CSV file during spider crawl.
    Support writing multiple item types simultaneously.
    """
    def __init__(self, spider: Spider):
        super().__init__(spider)
        if not self.settings.get('FILES_DIR'):
            raise ValueError('FILES_DIR not specified in settings')

        self.csv_dir: Path = self.settings['FILES_DIR'] / spider.state_code
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Using {self.csv_dir} as dir for CSV export")

        self.csv_writer_by_type: dict[str, CsvWriterWrapper] = {}

    def process_item(self, item: CaseItem, spider):
        self.logger.info(f"item: {item}")
        # use item._type to group items, or just spider.name
        from dataclasses import asdict
        self.logger.info(f"item: {item}")
        if isinstance(item, CaseItem):
            item_type = 'Cases'
        elif isinstance(item, DocumentItem):
            item_type = 'Documents'
        else:
            raise TypeError(f'Unrecognized item type: {item}')

        item_dict = asdict(item)
        self.logger.info(f"item_dict: {item_dict}")
        csv_row = item_dict | item_dict.pop('state_specific_info')

        # get CSV file writer for item type, or start a new one
        csv_writer: CsvWriterWrapper = self.csv_writer_by_type.get(item_type)
        if csv_writer is None:
            csv_writer = self._open_csv_writer(csv_name=item_type, fieldnames=list(csv_row.keys()), write_header=True)
            self.csv_writer_by_type[item_type] = csv_writer

        # write item to CSV
        csv_writer.writerow(csv_row)
        return item

    def close_spider(self, spider):
        for csv_writer in self.csv_writer_by_type.values():
            csv_writer.close()

    def _open_csv_writer(self, csv_name: str, fieldnames: list[str], write_header: bool = False) -> 'CsvWriterWrapper':
        csv_path = self.csv_dir / f'{csv_name.lower()}.csv'
        self.logger.info(f"Opening CSV writer at {csv_path} with fieldnames:\n {','.join(fieldnames)}")
        csv_writer = CsvWriterWrapper(csv_path=csv_path, fieldnames=fieldnames, override=False)
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


class CaseDbPipeline(BasePipeline):
    def process_item(self, item: CaseItemCT | CaseItemNY, spider: Spider):
        # convert item to Case model
        case: Case = item.to_record()

        # save Case
        case.save()
        self.logger.info(f"Saved Case: {case.id}")

        # save state-specific CaseDetails
        if hasattr(case, 'ct_details'):
            case.ct_details.save()
            self.logger.info(f"Saved CaseDetailsCT: {case.ct_details.id}")

        elif hasattr(case, 'ny_details'):
            case.ny_details.save()
            self.logger.info(f"Saved CaseDetailsNY: {case.ny_details.id}")


# - - - - - - - - - - - - - - - - - -
# RNS DETAIL SPIDER PIPELINES
class ArticleS3UploadPipeline(BasePipeline):
    """
    Pipeline for saving article content to S3 bucket.
    Processes ArticleTextItem items by saving their content (HTML or PDF) to the specified S3 bucket,
    organizing it by company directory structure.

    Attributes:
        s3_bucket_name (str): Name of the S3 bucket to save articles.
        article_bucket (): boto3 S3 bucket object.
    """
    def __init__(self, spider):
        super().__init__(spider)
        aws_key_id, aws_secret_key = self.settings.get('AWS_ACCESS_KEY_ID'), self.settings.get('AWS_SECRET_ACCESS_KEY')
        if not aws_key_id or not aws_secret_key:
            raise ValueError('AWS credentials are incomplete')

        self.s3_bucket_name = self.settings.get('ARTICLES_S3_BUCKET_NAME')
        if not self.s3_bucket_name:
            raise ValueError('AWS S3 bucket name is not defined')

        s3 = boto3.resource('s3', aws_access_key_id=aws_key_id, aws_secret_access_key=aws_secret_key)
        self.article_bucket = s3.Bucket(self.s3_bucket_name)

    def process_item(self, item, spider):
        item.relative_path = f"{spider.exchange_key}/{item.symbol}/{item.article_id}.{item.content_type}"
        try:
            self.article_bucket.put_object(Key=item.relative_path, Body=item.content)
            self.logger.info(f"Uploaded to S3 {self.s3_bucket_name} at {item.relative_path}")
        except Exception as e:
            self.logger.error(f"Failed to save {item.relative_path} to S3: {e}")
        return item