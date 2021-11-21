import os
import pathlib
import re
import tempfile
from operator import attrgetter

import palettable


def get_cache_dir():
    path = pathlib.Path(os.path.join(tempfile.gettempdir(), "localtileserver"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_file_from_request(response):
    d = response.headers["content-disposition"]
    fname = re.findall("filename=(.+)", d)[0]
    path = get_cache_dir() / fname
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def is_valid_palette(palette: str):
    try:
        attrgetter(palette)(palettable)
    except AttributeError:
        return False
    return True
