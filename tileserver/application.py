import io
import json

from flask import Flask, render_template, request, send_file
from flask.views import View
from flask_caching import Cache
from large_image_source_gdal import GDALFileTileSource
from werkzeug.routing import FloatConverter as BaseFloatConverter

from . import large_image_utilities


class FloatConverter(BaseFloatConverter):
    regex = r"-?\d+(\.\d+)?"


app = Flask(__name__)

app.url_map.converters["float"] = FloatConverter
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})


class BaseTileView(View):
    def get_tile_source(self):
        """Return the built tile source."""
        projection = request.args.get("projection", "EPSG:3857")
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
            if palette:
                style["palette"] = palette
            nodata = request.args.get("nodata", None)
            if nodata:
                style["nodata"] = nodata
            style = json.dumps(style)

        path = app.config["path"]
        return large_image_utilities.get_tilesource_from_image(
            path, projection, style=style
        )


class TileMetadataView(BaseTileView):
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        metadata = tile_source.getMetadata()
        return metadata


class TileInternalMetadataView(BaseTileView):
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        metadata = tile_source.getInternalMetadata()
        return metadata


class TilesView(BaseTileView):
    @cache.cached(timeout=120)
    def dispatch_request(self, x: int, y: int, z: int):
        tile_source = self.get_tile_source()
        tile_binary = tile_source.getTile(x, y, z)
        mime_type = tile_source.getTileMimeType()
        return send_file(
            io.BytesIO(tile_binary),
            attachment_filename=f"{x}.{y}.{z}.png",
            mimetype=mime_type,
        )


class ThumbnailView(BaseTileView):
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
            raise TypeError("Souce image must have geospatial reference.")
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
            # attachment_filename=os.path.basename(path),
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
            # attachment_filename=os.path.basename(path),
            mimetype=mime_type,
        )


class Viewer(View):
    def dispatch_request(self):
        return render_template("tileviewer.html")


app.add_url_rule("/", view_func=Viewer.as_view("index"))
app.add_url_rule("/metadata", view_func=TileMetadataView.as_view("metadata"))
app.add_url_rule(
    "/metadata/internal",
    view_func=TileInternalMetadataView.as_view("internal-metadata"),
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
    path = app.config["path"]
    tile_source = large_image_utilities.get_tilesource_from_image(path, "EPSG:3857")
    context = tile_source.getMetadata()
    context["path"] = path
    return context
