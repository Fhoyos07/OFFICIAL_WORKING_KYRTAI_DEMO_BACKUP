from scrapy import Item, Field
from itemloaders import ItemLoader
from collections import defaultdict
from .utils.scrapy.item_processors import string_cell


class DynamicItem(Item):
    """
    Dynamic item - doesn't require specifying fields
    """
    fields = defaultdict(Field)


class DynamicItemLoader(ItemLoader):
    """
    Dynamic item loader - doesn't require specifying fields and process values as string by default
    """
    default_item_class = DynamicItem
    default_output_processor = string_cell
