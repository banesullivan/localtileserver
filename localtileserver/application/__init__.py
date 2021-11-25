from flask import Flask

app = Flask(__name__)

from tileserver.application import rest, urls, views  # noqa
