from itemadapter import ItemAdapter
from scrapy.crawler import Crawler
from pathlib import Path
from scrapy import Spider
import json

from .utils.scrapy.pipelines import CsvWriterWrapper


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

    def process_item(self, item, spider):
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
