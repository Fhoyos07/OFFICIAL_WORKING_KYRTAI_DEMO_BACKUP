from itemadapter import ItemAdapter
from scrapy.crawler import Crawler
from pathlib import Path
from scrapy import Spider
import json

from django.db import models, transaction, connection
from django.utils import timezone

from utils.scrapy.pipelines import CsvWriterWrapper
from apps.web.models import Case, Document
from .items import DbItem, DocumentBodyItem
from .spiders._base import BaseCaseSearchSpider, BaseCaseDetailSpider, BaseDocumentDownloadSpider


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


class CaseSearchDbPipeline(BasePipeline):
    def __init__(self, spider: BaseCaseSearchSpider):
        super().__init__(spider)
        self.cases_to_create: list[Case] = []
        self.chunk_size = 200

        # relation from Case to CaseDetail state object (i.e., ny_details)
        self.case_detail_relation: str = spider.case_detail_relation

    def process_item(self, item: DbItem, spider: BaseCaseSearchSpider):
        # convert item to Case model and append to list for bulk processing
        case: Case = item.record
        self.cases_to_create.append(case)

        if len(self.cases_to_create) >= self.chunk_size:
            self.insert_cases()
        return item

    def close_spider(self, spider: BaseCaseSearchSpider):
        self.insert_cases()

    # @transaction.atomic()
    def insert_cases(self):
        if not self.cases_to_create: return

        Case.objects.bulk_create(self.cases_to_create)

        case_details_to_create = [getattr(case, self.case_detail_relation) for case in self.cases_to_create]
        case_detail_model = type(case_details_to_create[0])
        case_detail_model.objects.bulk_create(case_details_to_create)

        self.logger.info(f'Saved {len(self.cases_to_create)} Cases and {len(case_details_to_create)} Details')
        self.cases_to_create = []


class CaseDetailDbPipeline(BasePipeline):
    def __init__(self, spider: BaseCaseSearchSpider):
        super().__init__(spider)
        self.documents_to_create: list[Document] = []
        self.chunk_size = 200

        # relation from Case to CaseDetail state object (i.e., ny_details)
        self.case_detail_relation: str = spider.case_detail_relation
        self.document_detail_relation: str = spider.document_detail_relation

    def process_item(self, item: DbItem, spider: BaseCaseSearchSpider):
        # convert item to Case model and append to list for bulk processing
        record: Case | Document = item.record
        if isinstance(record, Case):
            self.update_case(case=record)
        elif isinstance(record, Document):
            self.documents_to_create.append(record)
        else:
            raise TypeError(f'Invalid type: {record}')

        if len(self.documents_to_create) >= self.chunk_size:
            self.create_documents()
        return item

    def close_spider(self, spider: BaseCaseSearchSpider):
        self.create_documents()

    def update_case(self, case: Case):
        case.save()

        case_detail = getattr(case, self.case_detail_relation)
        case_detail.save()

    # @transaction.atomic()
    def create_documents(self):
        if not self.documents_to_create: return

        Document.objects.bulk_create(self.documents_to_create)

        document_details_to_create = [getattr(case, self.case_detail_relation) for case in self.documents_to_create]
        document_detail_model = type(document_details_to_create[0])
        document_detail_model.objects.bulk_create(document_details_to_create)

        self.logger.info(f'Saved {len(self.documents_to_create)} Documents and {len(document_details_to_create)} Details')
        self.documents_to_create = []


class DocumentS3UploadPipeline(BasePipeline):
    """
    Pipeline for saving article content to S3 bucket.
    Processes ArticleTextItem items by saving their content (HTML or PDF) to the specified S3 bucket,
    organizing it by company directory structure.

    Attributes:
        s3_bucket_name (str): Name of the S3 bucket to save articles.
        article_bucket (): boto3 S3 bucket object.
    """
    def __init__(self, spider: BaseDocumentDownloadSpider):
        super().__init__(spider)
        import boto3
        aws_key_id, aws_secret_key = self.settings.get('AWS_ACCESS_KEY_ID'), self.settings.get('AWS_SECRET_ACCESS_KEY')
        if not aws_key_id or not aws_secret_key:
            raise ValueError('AWS credentials are incomplete')

        self.s3_bucket_name = self.settings.get('AWS_S3_BUCKET_NAME')
        if not self.s3_bucket_name:
            raise ValueError('AWS S3 bucket name is not defined')

        s3 = boto3.resource('s3', aws_access_key_id=aws_key_id, aws_secret_access_key=aws_secret_key)
        self.article_bucket = s3.Bucket(self.s3_bucket_name)

    def process_item(self, item: DocumentBodyItem, spider: BaseDocumentDownloadSpider):
        document: Document = item.record
        relative_path = f"{spider.state_code}/{document.case.docket_id}/{document.document_id}.pdf"
        try:
            self.article_bucket.put_object(Key=relative_path, Body=item.body)
            self.logger.info(f"Uploaded to S3 {self.s3_bucket_name} at {relative_path}")
            item.relative_path = relative_path
        except Exception as e:
            self.logger.error(f"Failed to save {relative_path} to S3: {e}")
        return item


class DocumentDbPipeline(BasePipeline):
    def __init__(self, spider: BaseDocumentDownloadSpider):
        super().__init__(spider)
        self.documents_to_update: list[Document] = []
        self.chunk_size = 200

    def process_item(self, item: DocumentBodyItem, spider: BaseDocumentDownloadSpider):
        if item.relative_path:
            document: Document = item.record
            document.is_downloaded = True
            document.download_date = timezone.now()
            document.relative_path = item.relative_path
            self.documents_to_update.append(document)

        if len(self.documents_to_update) >= self.chunk_size:
            self.update_documents()
        return item

    def close_spider(self, spider: BaseCaseSearchSpider):
        self.update_documents()

    def update_documents(self):
        if not self.documents_to_update: return
        Document.objects.bulk_update(self.documents_to_update, fields=['is_downloaded', 'relative_path'])
        self.logger.info(f'Updated {len(self.documents_to_update)} Documents')


# class LoggingPipeline:
#     def process_item(self, item, spider):
#         item_dict = ItemAdapter(item).asdict()
#         spider.logger.info(json.dumps(item_dict, indent=2))
#         return item
#
#
# class DocumentSavePipeline(BasePipeline):
#     def __init__(self, spider: Spider):
#         super().__init__(spider)
#         self.pdf_dir = Path(self.settings['FILES_DIR']) / spider.state_code / 'pdfs'
#
#     def process_item(self, item: dict, spider: Spider):
#         # generate pdf path
#         pdf_path = self.pdf_dir / item['relative_file_path']
#         pdf_path.parent.mkdir(parents=True, exist_ok=True)
#
#         # save to file
#         with open(pdf_path, 'wb') as file:
#             file.write(item['body'])
#         self.logger.debug(f"Wrote to {pdf_path}")
#
#
# class CsvPipeline(BasePipeline):
#     """
#     Pipeline for writing to CSV file during spider crawl.
#     Support writing multiple item types simultaneously.
#     """
#     def __init__(self, spider: Spider):
#         super().__init__(spider)
#         if not self.settings.get('FILES_DIR'):
#             raise ValueError('FILES_DIR not specified in settings')
#
#         self.csv_dir: Path = self.settings['FILES_DIR'] / spider.state_code
#         self.csv_dir.mkdir(parents=True, exist_ok=True)
#         self.logger.info(f"Using {self.csv_dir} as dir for CSV export")
#
#         self.csv_writer_by_type: dict[str, CsvWriterWrapper] = {}
#
#     def process_item(self, item: CaseItem, spider):
#         self.logger.info(f"item: {item}")
#         # use item._type to group items, or just spider.name
#         from dataclasses import asdict
#         self.logger.info(f"item: {item}")
#         if isinstance(item, CaseItem):
#             item_type = 'Cases'
#         elif isinstance(item, DocumentItem):
#             item_type = 'Documents'
#         else:
#             raise TypeError(f'Unrecognized item type: {item}')
#
#         item_dict = asdict(item)
#         self.logger.info(f"item_dict: {item_dict}")
#         csv_row = item_dict | item_dict.pop('state_specific_info')
#
#         # get CSV file writer for item type, or start a new one
#         csv_writer: CsvWriterWrapper = self.csv_writer_by_type.get(item_type)
#         if csv_writer is None:
#             csv_writer = self._open_csv_writer(csv_name=item_type, fieldnames=list(csv_row.keys()), write_header=True)
#             self.csv_writer_by_type[item_type] = csv_writer
#
#         # write item to CSV
#         csv_writer.writerow(csv_row)
#         return item
#
#     def close_spider(self, spider):
#         for csv_writer in self.csv_writer_by_type.values():
#             csv_writer.close()
#
#     def _open_csv_writer(self, csv_name: str, fieldnames: list[str], write_header: bool = False) -> 'CsvWriterWrapper':
#         csv_path = self.csv_dir / f'{csv_name.lower()}.csv'
#         self.logger.info(f"Opening CSV writer at {csv_path} with fieldnames:\n {','.join(fieldnames)}")
#         csv_writer = CsvWriterWrapper(csv_path=csv_path, fieldnames=fieldnames, override=False)
#         if write_header:
#             csv_writer.writeheader()
#         return csv_writer
#
#
# class CsvOnClosePipeline(CsvPipeline):
#     """
#     Pipeline for writing to CSV file, collecting all items and writing them at once on spider finish.
#     Support writing only 1 writing type.
#     """
#     def __init__(self, spider: Spider):
#         super().__init__(spider)
#         self.items = []
#
#     def process_item(self, item, spider):
#         self.items.append(item)
#         return item
#
#     def close_spider(self, spider):
#         fields_to_export = self.collect_fields(self.items)
#         csv_writer = self._open_csv_writer(csv_name=spider.name,
#                                            fieldnames=fields_to_export,
#                                            write_header=True)
#         csv_writer.writerows(self.items)
#         csv_writer.close()
#
#     @staticmethod
#     def collect_fields(items: list[dict]) -> list[str]:
#         """Get list of all fields from all items (used as csv header)"""
#         fields = []
#         for item in items:
#             for field in item:
#                 if field not in fields:
#                     fields.append(field)
#         return fields
