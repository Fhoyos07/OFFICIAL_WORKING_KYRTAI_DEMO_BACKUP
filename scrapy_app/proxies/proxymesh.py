__author__ = 'mizhgun@gmail.com'
from scrapy.utils.misc import arg_to_iter
import itertools
import base64
from urllib.request import getproxies, proxy_bypass, _parse_proxy
from urllib.parse import unquote, urlunparse
from scrapy.exceptions import NotConfigured


class ProxyMeshMiddleware(object):
    def __init__(self, settings):
        if not settings.getbool('PROXYMESH_ENABLED', True):
            raise NotConfigured
        self.proxies = itertools.cycle(arg_to_iter(settings.get('PROXYMESH_URL')))
        self.timeout = settings.getint('PROXYMESH_TIMEOUT', 0)

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings)
        return o

    def _get_proxy(self, url):
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse((proxy_type, hostport, '', '', '', ''))

        if user and password:
            user_pass = '%s:%s' % (unquote(user), unquote(password))
            creds = base64.b64encode(user_pass).strip()
        else:
            creds = None

        return creds, proxy_url

    def process_request(self, request, spider):
        if not request.meta.get('bypass_proxy', False) and request.meta.get('proxy') is None:
            creds, proxy = self._get_proxy(self.proxies.next())
            request.meta['proxy'] = proxy
            if creds:
                request.headers['Proxy-Authorization'] = b'Basic ' + creds
            if self.timeout and not request.headers.get('X-ProxyMesh-Timeout'):
                request.headers.update({'X-ProxyMesh-Timeout': self.timeout})