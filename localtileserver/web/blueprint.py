from flask import Blueprint
from flask_caching import Cache

tileserver = Blueprint(
    "tileserver",
    __name__,
    static_folder="static",
    static_url_path="/static/tileserver",
    template_folder="templates",
)


cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
