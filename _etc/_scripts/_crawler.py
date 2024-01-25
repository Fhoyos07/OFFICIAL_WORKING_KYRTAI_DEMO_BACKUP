from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os
import sys


def crawl(spider_name: str):
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))   # set working dir to project root
    os.chdir(project_dir)
    sys.path.append(project_dir)

    process = CrawlerProcess(get_project_settings(), install_root_handler=False)
    process.crawl(spider_name)
    process.start()  # script will block here until crawling finish
