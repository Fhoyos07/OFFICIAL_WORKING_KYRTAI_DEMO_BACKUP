import base64


class SmartProxyMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.enabled = settings.get('SMARTPROXY_ENABLED') is True

        self.user = settings.get('SMARTPROXY_USER')
        self.password = settings.get('SMARTPROXY_PASSWORD')
        self.endpoint = settings.get('SMARTPROXY_ENDPOINT')
        self.port = settings.get('SMARTPROXY_PORT')

        user_credentials = f'{self.user}:{self.password}'
        self.auth_header = f'Basic {base64.b64encode(user_credentials.encode()).decode()}'
        self.proxy = 'http://{endpoint}:{port}'.format(endpoint=self.endpoint, port=self.port)

    def process_request(self, request, spider):
        if not self.enabled: return

        request.meta['proxy'] = self.proxy
        request.headers['Proxy-Authorization'] = self.auth_header
