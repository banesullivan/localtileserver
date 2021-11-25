import logging
import pathlib

import click

from tileserver.application import app


@click.command()
@click.argument("filename")
@click.option("-p", "--port", default=0)
@click.option("-d", "--debug", default=False)
def run_app(filename, port=0, debug=False):
    filename = pathlib.Path(filename).expanduser().absolute()
    if not filename.exists():
        raise OSError(f"File does not exist: {filename}")
    app.config["DEBUG"] = debug
    app.config["filename"] = filename
    if debug:
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)
        logging.getLogger("gdal").setLevel(logging.DEBUG)
        logging.getLogger("large_image").setLevel(logging.DEBUG)
    app.run(host="localhost", port=port)


if __name__ == "__main__":
    run_app()
