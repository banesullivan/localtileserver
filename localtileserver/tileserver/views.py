import logging

from flask import current_app, render_template, request
from flask.views import View
from large_image.exceptions import TileSourceFileNotFoundError

from localtileserver.tileserver import utilities
from localtileserver.tileserver.blueprint import tileserver
from localtileserver.tileserver.data import get_data_path

logger = logging.getLogger(__name__)


def _get_clean_filename_from_request():
    try:
        # First look for filename in URL params
        f = request.args.get("filename")
        if not f:
            raise KeyError
        filename = utilities.get_clean_filename(f)
    except KeyError:
        # Backup to app.config
        try:
            filename = utilities.get_clean_filename(current_app.config["filename"])
        except KeyError:
            # Fallback to sample data
            logger.error("No filename set in app config or URL params. Using sample data.")
            filename = get_data_path("landsat.tif")
    return filename


class BaseViewer(View):
    def render_or_404(self, template: str):
        """Check the file in the arguments and 404 if invalid."""
        projection = request.args.get("projection", None)
        # Check opening the file with large image
        try:
            filename = _get_clean_filename_from_request()
            _ = utilities.get_tile_source(filename, projection=projection)
        except (OSError, AttributeError, TileSourceFileNotFoundError):
            return render_template("tileserver/404file.html"), 404
        return render_template(template)


class GeoJSViewer(BaseViewer):
    def dispatch_request(self):
        return self.render_or_404("tileserver/geojsViewer.html")


class CesiumViewer(BaseViewer):
    def dispatch_request(self):
        return self.render_or_404("tileserver/cesiumViewer.html")


@tileserver.context_processor
def raster_context():
    try:
        filename = _get_clean_filename_from_request()
    except OSError:
        filename = request.args.get("filename", "")
    context = {}
    context["filename"] = filename
    try:
        tile_source = utilities.get_tile_source(filename)
    except (OSError, AttributeError, TileSourceFileNotFoundError):
        return context
    context.update(utilities.get_meta_data(tile_source))
    context["bounds"] = utilities.get_tile_bounds(tile_source, projection="EPSG:4326")
    return context


@tileserver.context_processor
def sample_data_context():
    context = {}
    context["filename_dem"] = get_data_path("aws_elevation_tiles_prod.xml")
    context["filename_bluemarble"] = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    context["filename_virtualearth"] = get_data_path("frmt_wms_virtualearth.xml")
    context["cesium_token"] = current_app.config.get("cesium_token", "")
    return context
