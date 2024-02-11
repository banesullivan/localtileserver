import os

from flask import Blueprint
from flask_caching import Cache

tileserver = Blueprint(
    "tileserver",
    __name__,
    static_folder="static",
    static_url_path="/static/tileserver",
    template_folder="templates",
)


def get_memcache_config():
    url, username, password = None, None, None
    if os.environ.get("MEMCACHED_URL", ""):
        url = os.environ.get("MEMCACHED_URL")
        if os.environ.get("MEMCACHED_USERNAME", "") and os.environ.get("MEMCACHED_PASSWORD", ""):
            username = os.environ.get("MEMCACHED_USERNAME")
            password = os.environ.get("MEMCACHED_PASSWORD")
    elif os.environ.get("MEMCACHIER_SERVERS", ""):
        url = os.environ.get("MEMCACHIER_SERVERS")
        if os.environ.get("MEMCACHIER_USERNAME", "") and os.environ.get("MEMCACHIER_PASSWORD", ""):
            username = os.environ.get("MEMCACHIER_USERNAME")
            password = os.environ.get("MEMCACHIER_PASSWORD")
    return url, username, password


def create_cache(url: str = None, username: str = None, password: str = None):
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
