from parsel.selector import Selector, SelectorList
from scrapy.http import HtmlResponse

from ..types.str import trim_spaces, format_key


def extract_text_from_el(el: Selector | SelectorList) -> str | None:
    """Extract all descendant text from Selector"""
    if not el: return
    if isinstance(el, SelectorList): el = el[0]

    el_xpath = el._expr
    if el_xpath.endswith('text()'):
        return el.get()

    text_parts = el.xpath('.//text()[normalize-space()]').getall()
    return trim_spaces(' '.join(text_parts))


def extract_rows_data_from_table(
        container: HtmlResponse,
        table_xpath: str,
        header_xpath: str = 'descendant::tr[1]/th',
        rows_xpath: str = 'descendant::tr[position()>1]'
) -> list[dict[str, str]]:
    """
    Extract data from HTML table to list of dicts (each element - table row)
    """
    table = container.xpath(table_xpath)
    table_headers = table.xpath(header_xpath)
    column_names = [format_key(extract_text_from_el(k)) for k in table_headers]

    data = []
    for row in table.xpath(rows_xpath):
        d = {}
        for i, td in enumerate(row.xpath('td')):
            key = column_names[i]
            value = extract_text_from_el(td)
            if not key:
                continue
            d[key] = value
        data.append(d)
    return data


def extract_attrs_data_from_table(response: HtmlResponse,
                                  rows_xpath: str,
                                  key_xpath: str,
                                  value_xpath: str) -> dict[str, str]:
    """Extract data from HTML key-value table to dict of attrs"""
    data = {}
    for r in response.xpath(rows_xpath):
        key_el, value_el = r.xpath(key_xpath), r.xpath(value_xpath)

        raw_key = extract_text_from_el(key_el)
        if not raw_key:
            raise KeyError(f'Not found key at {key_xpath}')
        key = format_key(raw_key)
        if not key: continue
        raw_value = extract_text_from_el(value_el)
        data[key] = trim_spaces(raw_value) if raw_value else None
    return data


def extract_form_data(response: HtmlResponse, form_xpath: str) -> dict[str, str]:
    """Extract data from HTML form to dict"""
    form_inputs = response.xpath(form_xpath).xpath('descendant::input[not(@type="button")][not(@type="submit")]')
    form_data = {el.xpath('@name').get(): el.xpath('@value').get() for el in form_inputs}
    return form_data
