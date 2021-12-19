import io
import time

from PIL import Image, ImageOps
from flask import request, send_file
from flask_restx import Api, Resource as View
from large_image_source_gdal import GDALFileTileSource

from localtileserver import __version__
from localtileserver.tileserver import style, utilities
from localtileserver.tileserver.blueprint import cache, tileserver
from localtileserver.tileserver.palettes import get_palettes

REQUEST_CACHE_TIMEOUT = 60 * 60 * 2

api = Api(tileserver, doc="/swagger/", title="localtileserver", version=__version__)

BASE_PARAMS = {
    "filename": {
        "description": "The local path or URL to the image to use.",
        "in": "query",
        "type": "str",
    },
    "projection": {
        "description": "The projection to open the image in (default is `EPSG:3857`).",
        "in": "query",
        "type": "str",
    },
}
STYLE_PARAMS = {
    "band": {
        "description": "The band number to use.",
        "in": "query",
        "type": "int",
    },
    "palette": {
        "description": "The color palette to map the band values (named Matplotlib colormaps or palettable palettes).",
        "in": "query",
        "type": "str",
    },
    "min": {
        "description": "The minimum value for the color mapping.",
        "in": "query",
        "type": "float",
    },
    "max": {
        "description": "The maximum value for the color mapping.",
        "in": "query",
        "type": "float",
    },
    "nodata": {
        "description": "The value to map as no data (often made transparent).",
        "in": "query",
        "type": "float",
    },
}
REGION_PARAMS = {
    "left": {
        "description": "The left bound (X).",
        "in": "query",
        "type": "float",
    },
    "right": {
        "description": "The right bound (X).",
        "in": "query",
        "type": "float",
    },
    "bottom": {
        "description": "The bottom bound (Y).",
        "in": "query",
        "type": "float",
    },
    "top": {
        "description": "The top bound (Y).",
        "in": "query",
        "type": "float",
    },
    "units": {
        "description": "The projection/units of the coordinates (default is `EPSG:4326`)",
        "in": "query",
        "type": "str",
    },
    "encoding": {
        "description": "The encoding of the output image (default is `TILED`)",
        "in": "query",
        "type": "str",
    },
}


def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args).encode("utf-8")


class ListColors(View):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT)
    def get(self):
        return get_palettes()


@api.doc(params=BASE_PARAMS)
class BaseImageView(View):
    def get_tile_source(self, projection="EPSG:3857"):
        """Return the built tile source."""
        filename = utilities.get_clean_filename_from_request()
        projection = request.args.get("projection", projection)
        style_args = style.reformat_style_query_parameters(request.args)
        band = style_args.get("band", 0)
        vmin = style_args.get("min", None)
        vmax = style_args.get("max", None)
        palette = style_args.get("palette", None)
        nodata = style_args.get("nodata", None)
        sty = style.make_style(band, vmin=vmin, vmax=vmax, palette=palette, nodata=nodata)
        return utilities.get_tile_source(filename, projection, style=sty)


class MetadataView(BaseImageView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self):
        tile_source = self.get_tile_source()
        return utilities.get_meta_data(tile_source)


@api.doc(
    params={
        "units": {
            "description": "The projection of the bounds (default is `EPSG:4326`).",
            "in": "query",
            "type": "str",
        }
    }
)
class BoundsView(BaseImageView):
    def get(self):
        tile_source = self.get_tile_source()
        # Override default projection for bounds
        units = request.args.get("units", "EPSG:4326")
        return utilities.get_tile_bounds(
            tile_source,
            projection=units,
        )


class ThumbnailView(BaseImageView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self):
        tile_source = self.get_tile_source()
        thumb_data, mime_type = tile_source.getThumbnail(encoding="PNG")
        return send_file(
            io.BytesIO(thumb_data),
            download_name="thumbnail.png",
            mimetype=mime_type,
        )


@api.doc(params=STYLE_PARAMS)
class BaseTileView(BaseImageView):
    @staticmethod
    def add_border_to_image(content):
        img = Image.open(io.BytesIO(content))
        img = ImageOps.crop(img, 1)
        border = ImageOps.expand(img, border=1, fill="black")
        img_bytes = io.BytesIO()
        border.save(img_bytes, format="PNG")
        return img_bytes.getvalue()


@api.doc(
    params={
        "sleep": {
            "description": "The time in seconds to delay serving each tile (useful when debugging to slow things down).",
            "in": "query",
            "type": "float",
        }
    }
)
class TileDebugView(View):
    """A dummy tile server endpoint that produces borders of the tile grid.

    This is used for testing tile viewers. It returns the same thing on every
    call. This takes a query parameter `sleep` to delay the response for
    testing (default is 0.5).

    """

    def get(self, x: int, y: int, z: int):
        img = Image.new("RGBA", (254, 254))
        img = ImageOps.expand(img, border=1, fill="black")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        time.sleep(float(request.args.get("sleep", 0.5)))
        return send_file(
            img_bytes,
            download_name=f"{x}.{y}.{z}.png",
            mimetype="image/png",
        )


@api.doc(
    params={
        "grid": {
            "description": "Show a grid/outline around each tile. This is useful for debugging viewers.",
            "in": "query",
            "type": "bool",
        }
    }
)
class TileView(BaseTileView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self, x: int, y: int, z: int):
        tile_source = self.get_tile_source()
        tile_binary = tile_source.getTile(x, y, z)
        mime_type = tile_source.getTileMimeType()
        grid = request.args.get("grid", "False")
        if grid.lower() in ["false", "no", "off"]:
            grid = False
        if grid:
            tile_binary = self.add_border_to_image(tile_binary)
        return send_file(
            io.BytesIO(tile_binary),
            download_name=f"{x}.{y}.{z}.png",
            mimetype=mime_type,
        )


@api.doc(params=REGION_PARAMS)
class BaseRegionView(BaseImageView):
    def get_bounds(self):
        left = float(request.args.get("left"))
        right = float(request.args.get("right"))
        bottom = float(request.args.get("bottom"))
        top = float(request.args.get("top"))
        return (left, right, bottom, top)


class RegionWorldView(BaseRegionView):
    """Returns region tile binary from world coordinates in given EPSG.

    Use the `units` query parameter to inidicate the projection of the given
    coordinates. This can be different than the `projection` parameter used
    to open the tile source. `units` defaults to `EPSG:4326`.

    """

    def get(self):

        tile_source = self.get_tile_source()
        if not isinstance(tile_source, GDALFileTileSource):
            raise TypeError("Source image must have geospatial reference.")
        units = request.args.get("units", "EPSG:4326")
        encoding = request.args.get("encoding", "TILED")
        left, right, bottom, top = self.get_bounds()
        path, mime_type = utilities.get_region_world(
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


class RegionPixelView(BaseRegionView):
    """Returns region tile binary from pixel coordinates."""

    def get(self):
        tile_source = self.get_tile_source()
        encoding = request.args.get("encoding", None)
        left, right, bottom, top = self.get_bounds()
        path, mime_type = utilities.get_region_pixel(
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
