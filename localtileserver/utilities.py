import pathlib
import re
from urllib.parse import urlencode

import requests

from localtileserver.tiler import get_cache_dir


def save_file_from_request(response: requests.Response, output_path: pathlib.Path):
    d = response.headers["content-disposition"]
    fname = re.findall("filename=(.+)", d)[0]
    if isinstance(output_path, bool) or not output_path:
        output_path = get_cache_dir() / fname
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def add_query_parameters(url: str, params: dict):
    if len(params) and "?" not in url:
        url += "?"
    for k, v in params.items():
        if isinstance(v, (list, tuple)):
            for i, sub in enumerate(v):
                url += "&" + urlencode({f"{k}.{i}": sub})
        else:
            url += "&" + urlencode({k: v})
    return url
