from scrapy import Spider, Request, FormRequest

from ..items import DynamicItemLoader
from ..utils.scrapy.decorators import log_response, save_response, log_method


class PrototypeSpider(Spider):
    name = 'prototype'

    def start_requests(self):
        url = 'http://quotes.toscrape.com'
        yield Request(url, callback=self.parse_list, errback=self.parse_error)

    @log_response
    @save_response
    def parse_list(self, response):
        for quote_row in response.css('.quote'):
            il = DynamicItemLoader(response=response, selector=quote_row)
            il.add_css('text', '[itemprop="text"]::text')  # , lambda x: [a.strip('“”') for a in x]
            il.add_css('author', '[itemprop="author"]::text')
            yield il.load_item()

        next_page_url = response.css('li.next a::attr(href)').get()
        if next_page_url:
            yield response.follow(next_page_url, callback=self.parse_list)

    @log_response
    @save_response
    def parse_error(self):
        pass
