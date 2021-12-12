from flask import Blueprint

from localtileserver.tileserver.utilities import get_memcache_config

tileserver = Blueprint(
    "tileserver",
    __name__,
    static_folder="static",
    static_url_path="/static/tileserver",
    template_folder="templates",
)


def create_cache(url: str, username: str = None, password: str = None):
    try:
        from flask_caching import MemcachedCache, SASLMemcachedCache

        if url:
            config = {"CACHE_MEMCACHED_SERVERS": url}
            if username and password:
                config["CACHE_MEMCACHED_USERNAME"] = username
                config["CACHE_MEMCACHED_PASSWORD"] = password
                cache = SASLMemcachedCache(config=config)
            else:
                cache = MemcachedCache(config=config)
        else:
            raise ImportError
    except ImportError:
        from flask_caching import Cache

        cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
    return cache


cache = create_cache(*get_memcache_config())
