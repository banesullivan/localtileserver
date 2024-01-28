import logging
import os
import socket
import threading
import webbrowser

import click
from flask import Flask
from flask_cors import CORS

from localtileserver.tiler import get_clean_filename
from localtileserver.web.blueprint import cache, tileserver


def create_app(
    url_prefix: str = "/", cors_all: bool = False, debug: bool = False, cesium_token: str = ""
):
    try:
        from localtileserver.web import sentry  # noqa: F401
    except Exception:
        pass
    app = Flask(__name__)
    if cors_all:
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    cache.init_app(app)
    app.register_blueprint(tileserver, url_prefix=url_prefix)
    app.config.JSONIFY_PRETTYPRINT_REGULAR = True
    app.config.SWAGGER_UI_DOC_EXPANSION = "list"
    app.config["DEBUG"] = debug
    app.config["cesium_token"] = cesium_token
    if debug:
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)
        logging.getLogger("rasterio").setLevel(logging.DEBUG)
        logging.getLogger("rio_tiler").setLevel(logging.DEBUG)
    return app


def run_app(
    filename,
    port: int = 0,
    debug: bool = False,
    browser: bool = True,
    cesium_token: str = "",
    host: str = "127.0.0.1",
    cors_all: bool = False,
    run: bool = True,
):
    """Serve tiles from the raster at `filename`.

    You can also pass the name of one of the example datasets: `elevation`,
    `blue_marble`, `virtual_earth`, `arcgis` or `bahamas`.

    """
    filename = get_clean_filename(filename)
    if not str(filename).startswith("/vsi") and not filename.exists():
        raise OSError(f"File does not exist: {filename}")
    app = create_app(cors_all=cors_all, debug=debug, cesium_token=cesium_token)
    app.config["filename"] = filename
    if os.name == "nt" and host == "127.0.0.1":
        host = "localhost"
    if port == 0:
        sock = socket.socket()
        sock.bind((host, 0))
        port = sock.getsockname()[1]
        sock.close()
    if browser:
        url = f"http://{host}:{port}?filename={filename}"
        threading.Timer(1, lambda: webbrowser.open(url)).start()
    if run:
        app.run(host=host, port=port, debug=debug)
    return app


@click.command()
@click.argument("filename")
@click.option("-p", "--port", default=0)
@click.option("-d", "--debug", default=False)
@click.option("-b", "--browser", default=True)
@click.option("-t", "--cesium-token", default="")
@click.option("-h", "--host", default="127.0.0.1")
@click.option("-c", "--cors-all", default=False)
def click_run_app(*args, **kwargs):
    return run_app(*args, **kwargs)
