# flake8: noqa: F401
from localtileserver.web import rest, urls, views
from localtileserver.web.application import create_app, run_app
from localtileserver.web.blueprint import cache, tileserver
