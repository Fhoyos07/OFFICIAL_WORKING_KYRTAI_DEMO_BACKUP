from dataclasses import dataclass
from typing import Type
from scrapy import Spider
from utils.scrapy.crawler import crawl_sequential

from utils.django import django_setup
django_setup()

from scraping_service.spiders.spider_ct import CtCaseSearchSpider, CtDocumentSpider
from scraping_service.spiders.spider_ny import KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider
from scraping_service.spiders.spider_ny_proceedings import KyrtNyProceedingSearchSpider, KyrtNyProceedingCaseSpider, KyrtNyDocumentProceedingSpider
import argparse


@dataclass
class SpiderConfiguration:
    spiders: list[Type[Spider]]


# Define the spider configurations
CONFIGURATIONS = {
    "NY": SpiderConfiguration(spiders=[
        KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider
    ]),
    "NY_proceedings": SpiderConfiguration(spiders=[
        KyrtNyProceedingSearchSpider, KyrtNyProceedingCaseSpider, KyrtNyDocumentProceedingSpider
    ]),
    "CT": SpiderConfiguration(spiders=[
        CtCaseSearchSpider, CtDocumentSpider
    ]),
}


def run_spiders(spiders):
    crawl_sequential(*spiders)


def get_all_spiders():
    all_spiders = []
    for config in CONFIGURATIONS.values():
        all_spiders.extend(config.spiders)
    return all_spiders


def main():
    parser = argparse.ArgumentParser(description="Run Scrapy spiders for different states.")
    parser.add_argument('name', nargs='?', choices=[*CONFIGURATIONS.keys(), 'ALL'], help='The name of the script to run')
    args = parser.parse_args()

    # Dynamically generate choices and matching cases
    selected_key = None
    if args.name:
        selected_key = args.name
    else:
        choices = [f"Press {index + 1} for {name}" for index, name in enumerate(['ALL', *CONFIGURATIONS.keys()])]
        choices_text = "\n".join(choices)
        choice_input = int(input(f"{choices_text}\nYour choice:\n"))
        if choice_input == 1:
            selected_key = 'ALL'
        elif 2 <= choice_input < len(CONFIGURATIONS) + 2:
            selected_key = list(CONFIGURATIONS.keys())[choice_input - 2]

    # run
    if selected_key == 'ALL':
        run_spiders(get_all_spiders())
    elif selected_key in CONFIGURATIONS:
        run_spiders(CONFIGURATIONS[selected_key].spiders)
    else:
        print("Invalid choice. Exiting.")


if __name__ == '__main__':
    main()
