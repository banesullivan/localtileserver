import logging
import os

from flask import current_app, render_template, request
from flask.views import View
from large_image.exceptions import TileSourceError

from localtileserver.tileserver import data, utilities
from localtileserver.tileserver.blueprint import tileserver

logger = logging.getLogger(__name__)


class BaseViewer(View):
    def render_or_404(self, template: str):
        """Check the file in the arguments and 404 if invalid."""
        projection = request.args.get("projection", None)
        # Check opening the file with large image
        try:
            filename = utilities.get_clean_filename_from_request()
            _ = utilities.get_tile_source(filename, projection=projection)
        except (OSError, AttributeError, TileSourceError):
            return render_template("tileserver/404file.html"), 404
        return render_template(template)


class GeoJSViewer(BaseViewer):
    def dispatch_request(self):
        return self.render_or_404("tileserver/geojsViewer.html")


class CesiumViewer(BaseViewer):
    def dispatch_request(self):
        return self.render_or_404("tileserver/cesiumViewer.html")


class CesiumSplitViewer(View):
    def dispatch_request(self):
        try:
            filename = utilities.get_clean_filename_from_request("filenameA", strict=True)
            _ = utilities.get_tile_source(filename)
        except (OSError, AttributeError, TileSourceError):
            f = request.args.get("filenameA")
            return render_template("tileserver/404file.html", filename=f), 404
        try:
            filename = utilities.get_clean_filename_from_request("filenameB", strict=True)
            _ = utilities.get_tile_source(filename)
        except (OSError, AttributeError, TileSourceError):
            f = request.args.get("filenameB")
            return render_template("tileserver/404file.html", filename=f), 404
        return render_template("tileserver/cesiumSplitViewer.html")


class SplitViewForm(View):
    def dispatch_request(self):
        return render_template("tileserver/splitForm.html")


@tileserver.context_processor
def raster_context():
    try:
        filename = utilities.get_clean_filename_from_request()
    except OSError:
        filename = request.args.get("filename", "")
    context = {}
    context["filename"] = filename
    try:
        tile_source = utilities.get_tile_source(filename)
    except (OSError, AttributeError, TileSourceError):
        return context
    context.update(utilities.get_meta_data(tile_source))
    context["bounds"] = utilities.get_tile_bounds(tile_source, projection="EPSG:4326")
    return context


@tileserver.context_processor
def sample_data_context():
    context = {}
    context["filename_dem"] = data.get_data_path("aws_elevation_tiles_prod.xml")
    context["filename_bluemarble"] = data.get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    context["filename_virtualearth"] = data.get_data_path("frmt_wms_virtualearth.xml")
    context["filename_pine_gulch"] = data.get_pine_gulch_url()
    context["filename_sf_bay"] = data.get_sf_bay_url()
    context["filename_landsat_salt_lake"] = data.get_data_path("landsat.tif")
    context["filename_oam2"] = data.get_oam2_url()
    context["cesium_token"] = current_app.config.get("cesium_token", "")
    return context


@tileserver.context_processor
def google_analytics_context():
    context = {}
    mid = os.environ.get("GOOGLE_ANALYTICS_MID", "")
    if mid:
        context["google_analytics_mid"] = mid
    return context
