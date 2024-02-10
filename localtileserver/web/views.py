import logging
import os

from flask import current_app, render_template, request
from flask.views import View
from rasterio.errors import RasterioIOError

from localtileserver.tiler import data
from localtileserver.tiler.handler import get_meta_data, get_reader, get_source_bounds
from localtileserver.web.blueprint import tileserver
from localtileserver.web.utils import get_clean_filename_from_request

logger = logging.getLogger(__name__)


class BaseViewer(View):
    def render_or_404(self, template: str):
        """Check the file in the arguments and 404 if invalid."""
        try:
            filename = get_clean_filename_from_request()
            _ = get_reader(filename)
        except (OSError, AttributeError, RasterioIOError):
            return render_template("tileserver/404file.html"), 404
        return render_template(template)


class CesiumViewer(BaseViewer):
    def dispatch_request(self):
        return self.render_or_404("tileserver/cesiumViewer.html")


class CesiumSplitViewer(View):
    def dispatch_request(self):
        try:
            filename = get_clean_filename_from_request("filenameA", strict=True)
            _ = get_reader(filename)
        except (OSError, AttributeError, RasterioIOError):
            f = request.args.get("filenameA")
            return render_template("tileserver/404file.html", filename=f), 404
        try:
            filename = get_clean_filename_from_request("filenameB", strict=True)
            _ = get_reader(filename)
        except (OSError, AttributeError, RasterioIOError):
            f = request.args.get("filenameB")
            return render_template("tileserver/404file.html", filename=f), 404
        return render_template("tileserver/cesiumSplitViewer.html")


class SplitViewForm(View):
    def dispatch_request(self):
        return render_template("tileserver/splitForm.html")


@tileserver.context_processor
def raster_context():
    try:
        filename = get_clean_filename_from_request()
    except OSError:
        filename = request.args.get("filename", "")
    context = {}
    context["filename"] = str(filename)
    try:
        tile_source = get_reader(filename)
    except (OSError, AttributeError, RasterioIOError):
        return context
    context.update(get_meta_data(tile_source))
    context["bounds"] = get_source_bounds(tile_source, projection="EPSG:4326")
    return context


@tileserver.context_processor
def sample_data_context():
    context = {}
    context["filename_dem"] = data.get_data_path("aws_elevation_tiles_prod.xml")
    context["filename_bluemarble"] = data.get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    context["filename_virtualearth"] = data.get_data_path("frmt_wms_virtualearth.xml")
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
