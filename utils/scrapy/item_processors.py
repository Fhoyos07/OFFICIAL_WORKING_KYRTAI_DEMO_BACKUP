from itemloaders.processors import MapCompose, Compose, Join, TakeFirst, Identity
from urllib.parse import urlparse, urljoin

from ..types.str import trim_spaces


class ToString:
    """Convert values to string"""
    def __call__(self, values):
        for v in values:
            yield str(v) if v is not None else ''


class RemoveSpaces:
    """Convert values to strings without spaces"""
    def __call__(self, values):
        for v in values:
            yield trim_spaces(v)


class ToLowerCase:
    """Convert values to lower case"""
    def __call__(self, values):
        for v in values:
            yield v.lower()


class ToFloat:
    """Convert values to float"""
    def __call__(self, values):
        for v in values:
            if v not in [None, '']:
                yield float(str(v))


class ToAbsoluteUrl:
    """Convert relative urls to absolute using response.urljoin"""
    def __call__(self, values, loader_context=None):
        from scrapy.http import Response
        response: Response = loader_context.get('response')
        for v in values:
            yield response.urljoin(v)


class RemoveQueryStringFromUrl:
    def __call__(self, values):
        for v in values:
            yield urljoin(v, urlparse(v).path)


class ToList:
    """Convert values to list"""
    def __call__(self, values):
        return [v for v in values]


class MakeUnique:
    """Remove duplicated values from list"""
    def __call__(self, values):
        return list(set(values))


# default combinations of output processors
string_cell = Compose(ToString(), RemoveSpaces(), TakeFirst())
list_cell = Compose(ToString(), RemoveSpaces(), MakeUnique(), Join(' | '))
