from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl


def parse_url_params(url: str) -> dict:
    """
    Parse url parameters as dict
    @param url: url. i.e., https://google.com?q=query&hl=en
    @return: params dict. i.e., {'q': 'query', 'hl': 'en'}
    """
    return dict(parse_qsl(urlparse(url).query))
