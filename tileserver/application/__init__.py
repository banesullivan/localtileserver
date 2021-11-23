from flask import Flask

app = Flask(__name__)

from tileserver.application import paths, rest, urls, views  # noqa
