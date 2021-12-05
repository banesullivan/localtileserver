# flake8: noqa: F401
from flask import Flask

app = Flask(__name__)

from localtileserver.application import rest, urls, views
