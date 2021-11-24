import logging

from flask import render_template
from flask.views import View

from tileserver import utilities
from tileserver.application import app
from tileserver.examples import get_data_path

logger = logging.getLogger(__name__)


class GeoJSViewer(View):
    def dispatch_request(self):
        return render_template("geojsViewer.html")


class CesiumViewer(View):
    def dispatch_request(self):
        return render_template("cesiumViewer.html")


@app.context_processor
def inject_context():
    try:
        filename = app.config["filename"]
    except KeyError:
        logger.error("No filename set in app config. Using sample data.")
        filename = get_data_path("bahamas_rgb.tif")
    tile_source = utilities.get_tile_source(filename)
    context = utilities.get_meta_data(tile_source)
    context["bounds"] = utilities.get_tile_bounds(tile_source, projection="EPSG:4326")
    context["filename"] = filename
    return context
