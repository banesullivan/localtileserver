# flake8: noqa: F401
from flask import Flask

from localtileserver.application import rest, urls, views
from localtileserver.application.blueprint import cache, tileserver
from localtileserver.application.utilities import get_cache_dir, make_vsi, purge_cache

app = Flask(__name__)
cache.init_app(app)
app.register_blueprint(tileserver, url_prefix="/")
