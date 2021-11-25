import logging
import os
import pathlib

import click

from localtileserver.application import app
from localtileserver.examples import get_data_path


@click.command()
@click.argument("filename")
@click.option("-p", "--port", default=0)
@click.option("-d", "--debug", default=False)
def run_app(filename, port=0, debug=False):
    """Serve tiles from the raster at `filename`.

    You can also pass the name of one of the example datasets: `elevation`,
    `blue_marble`, `virtual_earth`, `arcgis` or `bahamas`.

    """
    filename = pathlib.Path(filename).expanduser().absolute()
    if not filename.exists():
        name = os.path.basename(filename)
        if name == "blue_marble":
            filename = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
        elif name == "virtual_earth":
            filename = get_data_path("frmt_wms_virtualearth.xml")
        elif name == "arcgis":
            filename = get_data_path("frmt_wms_arcgis_mapserver_tms.xml")
        elif name in ["elevation", "dem", "topo"]:
            filename = get_data_path("aws_elevation_tiles_prod.xml")
        elif name == "bahamas":
            filename = get_data_path("bahamas_rgb.tif")
        else:
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
