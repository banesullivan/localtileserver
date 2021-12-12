from flask import Blueprint
from flask_caching import Cache

from localtileserver.tileserver.utilities import get_memcache_config

tileserver = Blueprint(
    "tileserver",
    __name__,
    static_folder="static",
    static_url_path="/static/tileserver",
    template_folder="templates",
)


def create_cache(url: str, username: str = None, password: str = None):
    if url:
        config = {"CACHE_MEMCACHED_SERVERS": url.split(",")}
        if username and password:
            config["CACHE_TYPE"] = "SASLMemcachedCache"
            config["CACHE_MEMCACHED_USERNAME"] = username
            config["CACHE_MEMCACHED_PASSWORD"] = password
        else:
            config["CACHE_TYPE"] = "MemcachedCache"

    else:
        config = {"CACHE_TYPE": "SimpleCache"}
    return Cache(config=config)


cache = create_cache(*get_memcache_config())
