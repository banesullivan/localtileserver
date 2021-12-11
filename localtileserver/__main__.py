import logging
import socket
import threading
import webbrowser

import click

from localtileserver.examples import get_pine_gulch_url
from localtileserver.tileserver import create_app, get_clean_filename, get_data_path


@click.command()
@click.argument("filename")
@click.option("-p", "--port", default=0)
@click.option("-d", "--debug", default=False)
@click.option("-b", "--browser", default=True)
def run_app(filename, port: int = 0, debug: bool = False, browser: bool = True):
    """Serve tiles from the raster at `filename`.

    You can also pass the name of one of the example datasets: `elevation`,
    `blue_marble`, `virtual_earth`, `arcgis` or `bahamas`.

    """
    # Check for example first
    if filename == "blue_marble":
        filename = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    elif filename == "virtual_earth":
        filename = get_data_path("frmt_wms_virtualearth.xml")
    elif filename == "arcgis":
        filename = get_data_path("frmt_wms_arcgis_mapserver_tms.xml")
    elif filename in ["elevation", "dem", "topo"]:
        filename = get_data_path("aws_elevation_tiles_prod.xml")
    elif filename == "bahamas":
        filename = get_data_path("bahamas_rgb.tif")
    elif filename == "pine_gulch":
        filename = get_pine_gulch_url()
    else:
        filename = get_clean_filename(filename)
        if not str(filename).startswith("/vsi") and not filename.exists():
            raise OSError(f"File does not exist: {filename}")
    app = create_app()
    app.config["DEBUG"] = debug
    app.config["filename"] = filename
    if debug:
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)
        logging.getLogger("gdal").setLevel(logging.DEBUG)
        logging.getLogger("large_image").setLevel(logging.DEBUG)
        logging.getLogger("large_image_source_gdal").setLevel(logging.DEBUG)

    if port == 0:
        sock = socket.socket()
        sock.bind(("localhost", 0))
        port = sock.getsockname()[1]
        sock.close()

    url = f"http://localhost:{port}"
    if browser:
        threading.Timer(1, lambda: webbrowser.open(url)).start()
    app.run(host="localhost", port=port, debug=debug)


if __name__ == "__main__":
    run_app()
