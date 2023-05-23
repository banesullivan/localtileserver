import pathlib
import re
from urllib.parse import urlencode

import requests

from localtileserver.tileserver import get_cache_dir


class ImageBytes(bytes):
    """Wrapper class to make repr of image bytes better in ipython."""

    def __new__(cls, source: bytes, mimetype: str = None):
        self = super().__new__(cls, source)
        self._mime_type = mimetype
        return self

    @property
    def mimetype(self):
        return self._mime_type

    def _repr_png_(self):
        if self.mimetype == "image/png":
            return self

    def _repr_jpeg_(self):
        if self.mimetype == "image/jpeg":
            return self

    def __repr__(self):
        if self.mimetype:
            return f"ImageBytes<{len(self)}> ({self.mimetype})"
        return f"ImageBytes<{len(self)}> (wrapped image bytes)"


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
