import os
import pathlib
import re
import tempfile


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
