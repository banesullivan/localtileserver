import requests


def get_content(url, timeout=5, **kwargs):
    r = requests.get(url, timeout=timeout, **kwargs)
    r.raise_for_status()
    return r.content
