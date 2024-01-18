import logging
from urllib.parse import urlsplit, urlunsplit


def format_url(url, replace_scheme: bool = False, remove_query: bool = False, remove_www: bool = True,
               lower: bool = True) -> str:
    u = urlsplit(url.strip())
    logging.debug(f'Converting {url} -> netloc "{u.netloc}", path: "{u.path}", query: "{u.query}"')

    # make url begin with "http"
    if replace_scheme:
        u = u._replace(scheme='http')

    # for urls with empty beginning - add "http"
    if not u.scheme:
        u = u._replace(scheme='http')

    # remove query from url
    if remove_query:
        u = u._replace(query=None)

    # for invalid urls (with empty netloc) - get it from path
    if not u.netloc:
        if '/' in u.path:
            netloc, path = u.path.split('/', 1)
            u = u._replace(netloc=netloc)
            u = u._replace(path='/' + path)
        else:
            u = u._replace(netloc=u.path)
            u = u._replace(path="")

    # add "/" to the end of path
    if not u.query:
        u = u._replace(path=u.path.rstrip('/') + '/')

    # remove "www" from url
    if u.netloc.startswith('www.') and remove_www:
        u = u._replace(netloc=u.netloc.replace('www.', '', 1))

    # join again
    url = urlunsplit(u)

    if lower:
        url = url.lower()

    logging.debug(f"Result: {url}")
    return url
