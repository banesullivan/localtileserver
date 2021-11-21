import io
import json
import logging

from flask import Flask, render_template, request, send_file
from flask.views import View
from flask_caching import Cache
from large_image_source_gdal import GDALFileTileSource
from werkzeug.routing import FloatConverter as BaseFloatConverter

from tileserver import large_image_utilities
from tileserver.application.paths import get_path
from tileserver.utilities import is_valid_palette

logger = logging.getLogger(__name__)


class FloatConverter(BaseFloatConverter):
    regex = r"-?\d+(\.\d+)?"


app = Flask(__name__)
app.url_map.converters["float"] = FloatConverter
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})


class BaseTileView(View):
    def get_tile_source(self, projection="EPSG:3857"):
        """Return the built tile source."""
        path = get_path()
        band = int(request.args.get("band", 0))
        style = None
        if band:
            style = {"band": band}
            bmin = request.args.get("min", None)
            bmax = request.args.get("max", None)
            if bmin is not None:
                style["min"] = bmin
            if bmax is not None:
                style["max"] = bmax
            palette = request.args.get("palette", None)
            if palette and is_valid_palette(palette):
                style["palette"] = palette
            elif palette:
                logger.error(
                    f"Palette choice of {palette} is invalid. Check available palettes in the `palettable` package."
                )
            nodata = request.args.get("nodata", None)
            if nodata:
                style["nodata"] = nodata
            style = json.dumps(style)

        return large_image_utilities.get_tilesource(path, projection, style=style)


class TileMetadataView(BaseTileView):
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        return large_image_utilities.get_meta_data(tile_source)


class TileBoundsView(BaseTileView):
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        projection = request.args.get("projection", "EPSG:4326")
        return tile_source.getBounds(srs=projection)


class TilesView(BaseTileView):
    @cache.memoize(timeout=120)
    def dispatch_request(self, x: int, y: int, z: int):
        projection = request.args.get("projection", "EPSG:3857")
        tile_source = self.get_tile_source(projection=projection)
        tile_binary = tile_source.getTile(x, y, z)
        mime_type = tile_source.getTileMimeType()
        return send_file(
            io.BytesIO(tile_binary),
            attachment_filename=f"{x}.{y}.{z}.png",
            mimetype=mime_type,
        )


class ThumbnailView(BaseTileView):
    @cache.memoize(timeout=120)
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        thumb_data, mime_type = tile_source.getThumbnail(encoding="PNG")
        return send_file(
            io.BytesIO(thumb_data),
            attachment_filename="thumbnail.png",
            mimetype=mime_type,
        )


class RegionWorldView(BaseTileView):
    """Returns region tile binary from world coordinates in given EPSG.

    Note
    ----
    Use the `units` query parameter to inidicate the projection of the given
    coordinates. This can be different than the `projection` parameter used
    to open the tile source. `units` defaults to `EPSG:4326`.

    """

    def dispatch_request(self, left: float, right: float, bottom: float, top: float):
        tile_source = self.get_tile_source()
        if not isinstance(tile_source, GDALFileTileSource):
            raise TypeError("Source image must have geospatial reference.")
        units = request.args.get("units", "EPSG:4326")
        encoding = request.args.get("encoding", "TILED")
        path, mime_type = large_image_utilities.get_region_world(
            tile_source,
            left,
            right,
            bottom,
            top,
            units,
            encoding,
        )
        return send_file(
            path,
            mimetype=mime_type,
        )


class RegionPixelView(BaseTileView):
    """Returns region tile binary from pixel coordinates."""

    def dispatch_request(self, left: float, right: float, bottom: float, top: float):
        tile_source = self.get_tile_source()
        encoding = request.args.get("encoding", None)
        path, mime_type = large_image_utilities.get_region_pixel(
            tile_source,
            left,
            right,
            bottom,
            top,
            encoding=encoding,
        )
        return send_file(
            path,
            mimetype=mime_type,
        )


class Viewer(View):
    def dispatch_request(self):
        return render_template("tileviewer.html")


app.add_url_rule("/", view_func=Viewer.as_view("index"))
app.add_url_rule("/metadata", view_func=TileMetadataView.as_view("metadata"))
app.add_url_rule(
    "/bounds",
    view_func=TileBoundsView.as_view("bounds"),
)
app.add_url_rule(
    "/tiles/<int:z>/<int:x>/<int:y>.png", view_func=TilesView.as_view("tiles")
)
app.add_url_rule("/thumbnail", view_func=ThumbnailView.as_view("thumbnail"))
app.add_url_rule(
    "/region/world/<float:left>/<float:right>/<float:bottom>/<float:top>/region.tif",
    view_func=RegionWorldView.as_view("region-world"),
)
app.add_url_rule(
    "/region/pixel/<int:left>/<int:right>/<int:bottom>/<int:top>/region.tif",
    view_func=RegionPixelView.as_view("region-pixel"),
)


@app.context_processor
def inject_context():
    path = get_path()
    tile_source = large_image_utilities.get_tilesource(path)
    context = large_image_utilities.get_meta_data(tile_source)
    context["bounds"] = large_image_utilities.get_tile_bounds(
        tile_source, projection="EPSG:4326"
    )
    context["path"] = path
    return context
