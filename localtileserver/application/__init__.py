from flask import Flask

app = Flask(__name__)

from localtileserver.application import rest, urls, views  # noqa
