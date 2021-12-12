from flask import Blueprint
from flask_caching import Cache, MemcachedCache

tileserver = Blueprint(
    "tileserver",
    __name__,
    static_folder="static",
    static_url_path="/static/tileserver",
    template_folder="templates",
)

def create_cache(url: str, username: str = None, password: str = None):
    if url:
        config = {"CACHE_MEMCACHED_SERVERS": url}
        if username and password:
            config["CACHE_MEMCACHED_USERNAME"] = username
            config["CACHE_MEMCACHED_PASSWORD"] = password
        cache = MemcachedCache(config=config)
    else:
        cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
    return cache
