"""URL and file utility functions for localtileserver."""

import pathlib
import re
from urllib.parse import urlencode

import requests

from localtileserver.tiler import get_cache_dir


def save_file_from_request(response: requests.Response, output_path: pathlib.Path):
    """
    Save the content of an HTTP response to a file on disk.

    The filename is extracted from the response's ``Content-Disposition``
    header. If ``output_path`` is falsy, the file is saved to the default
    cache directory.

    Parameters
    ----------
    response : requests.Response
        The HTTP response whose content will be written to disk.
    output_path : pathlib.Path
        The destination path for the saved file. If falsy, a path is
        generated from the cache directory and the response filename.

    Returns
    -------
    pathlib.Path
        The path to the saved file.
    """
    d = response.headers["content-disposition"]
    fname = re.findall("filename=(.+)", d)[0]
    if isinstance(output_path, bool) or not output_path:
        output_path = get_cache_dir() / fname
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def add_query_parameters(url: str, params: dict):
    """
    Append query parameters to a URL string.

    List or tuple values are joined with commas before encoding.

    Parameters
    ----------
    url : str
        The base URL to which parameters will be appended.
    params : dict
        A mapping of parameter names to values. Values may be strings,
        numbers, or sequences (list or tuple).

    Returns
    -------
    str
        The URL with the query parameters appended.
    """
    if len(params) and "?" not in url:
        url += "?"
    for k, v in params.items():
        if isinstance(v, (list, tuple)):
            url += "&" + urlencode({k: ",".join(str(s) for s in v)})
        else:
            url += "&" + urlencode({k: v})
    return url
