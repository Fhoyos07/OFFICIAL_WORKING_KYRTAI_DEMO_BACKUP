from dataclasses import dataclass, field
from typing import Type
from scrapy.spiders import Spider
from scrapy_app.utils.scrapy.crawler import crawl_sequential
# Assuming these imports are correct and the spiders are defined in your scrapy project
from scrapy_app.spiders.spider_ct import KyrtCtSearchSpider, KyrtCtDocumentSpider
from scrapy_app.spiders.spider_ny import KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider
from scrapy_app.spiders.spider_ny_proceedings import KyrtNyProceedingSearchSpider, KyrtNyProceedingCaseSpider, KyrtNyDocumentProceedingSpider
import argparse


@dataclass
class SpiderConfiguration:
    spiders: list[Type[Spider]]


# Define the spider configurations
configurations = {
    "NY": SpiderConfiguration(spiders=[
        KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider
    ]),
    "NY_proceedings": SpiderConfiguration(spiders=[
        KyrtNyProceedingSearchSpider, KyrtNyProceedingCaseSpider, KyrtNyDocumentProceedingSpider
    ]),
    "CT": SpiderConfiguration(spiders=[
        KyrtCtSearchSpider, KyrtCtDocumentSpider
    ]),
}


def run_spiders(spiders):
    crawl_sequential(*spiders)


def get_all_spiders():
    all_spiders = []
    for config in configurations.values():
        all_spiders.extend(config.spiders)
    return all_spiders


def main():
    parser = argparse.ArgumentParser(description="Run scrapy spiders for different states and proceedings.")
    parser.add_argument('name', nargs='?', choices=[*configurations.keys(), 'ALL'], help='The name of the script to run')
    args = parser.parse_args()

    # Dynamically generate choices and matching cases
    if args.name:
        if args.name == 'ALL':
            run_spiders(get_all_spiders())
        elif args.name in configurations:
            run_spiders(configurations[args.name].spiders)
    else:
        choices = [f"Press {index + 1} for {name}" for index, name in enumerate(['ALL', *configurations.keys()])]
        choices_text = "\n".join(choices)
        choice_input = int(input(f"{choices_text}\nYour choice:\n"))

        print(configurations)
        if choice_input == 1:
            run_spiders(get_all_spiders())
        elif 2 <= choice_input < len(configurations) + 2:
            selected = list(configurations.keys())[choice_input - 2]
            run_spiders(configurations[selected].spiders)
        else:
            print("Invalid choice. Exiting.")


if __name__ == '__main__':
    main()
