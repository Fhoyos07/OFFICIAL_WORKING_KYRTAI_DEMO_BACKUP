class ProxyMeshMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.enabled = settings.get('PROXYMESH_ENABLED') is True

        self.user = settings.get('PROXYMESH_USER')
        self.password = settings.get('PROXYMESH_PASSWORD')
        self.endpoint = settings.get('PROXYMESH_ENDPOINT')
        self.port = 31280

        self.proxy = f'http://{self.user}:{self.password}@{self.endpoint}:{self.port}'

    def process_request(self, request, spider):
        if not self.enabled: return

        if 'proxy' not in request.meta:
            request.meta['proxy'] = self.proxy


