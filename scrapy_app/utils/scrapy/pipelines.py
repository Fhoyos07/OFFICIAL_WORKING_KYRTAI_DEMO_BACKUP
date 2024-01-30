import os
import json
import csv
from scrapy.spiders import Spider
from dataclasses import dataclass
from itemadapter import ItemAdapter
from typing import IO
from pathlib import Path


@dataclass
class CsvWriterWrapper:
    _writer: csv.DictWriter
    _file: IO

    def __init__(self, csv_path: Path, fieldnames: list[str], encoding: str = 'utf-8'):
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
