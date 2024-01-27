from .utils.scrapy.pipelines import BasePipeline
from pathlib import Path
from scrapy import Spider


class DocumentSavePipeline(BasePipeline):
    def __init__(self, spider: Spider):
        super().__init__(spider)

        self.pdf_dir = Path(self.settings['FILES_DIR']) / 'pdfs'

    def process_item(self, item: dict, spider: Spider):
        # generate pdf path
        pdf_path = self.pdf_dir / item['relative_file_path']
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # save to file
        with open(pdf_path, 'wb') as file:
            file.write(item['body'])
        self.logger.debug(f"Wrote to {pdf_path}")
