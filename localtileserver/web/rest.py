import io
import pathlib
import time

from PIL import Image, ImageDraw, ImageOps
from flask import request, send_file
from flask_restx import Api, Resource as View
from rasterio import RasterioIOError
from rio_tiler.errors import TileOutsideBounds
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound

from localtileserver import __version__
from localtileserver.tiler import (
    format_to_encoding,
    get_meta_data,
    get_tile_bounds,
    get_tile_source,
)
from localtileserver.tiler.data import str_to_bool
from localtileserver.tiler.palettes import get_palettes
from localtileserver.web.blueprint import cache, tileserver
from localtileserver.web.utils import get_clean_filename_from_request

REQUEST_CACHE_TIMEOUT = 60 * 60 * 2

api = Api(
    tileserver,
    doc="/swagger/",
    title="localtileserver",
    version=__version__,
    default="localtileserver",
    default_label="localtileserver namespace",
    description="<a href='https://github.com/banesullivan/localtileserver' target='_blank'>Learn more about localtileserver</a>",
    prefix="api",
)

BASE_PARAMS = {
    "filename": {
        "description": "The local path or URL to the image to use.",
        "in": "query",
        "type": "str",
        "example": "https://data.kitware.com/api/v1/file/60747d792fa25629b9a79565/download",
    },
    "projection": {
        "description": "The projection in which to open the image.",
        "in": "query",
        "type": "str",
        "default": "EPSG:3857",
    },
}
STYLE_PARAMS = {
    "band": {
        "description": "The band number to use.",
        "in": "query",
        "type": "int",
    },
    "palette": {
        "description": "The color palette to map the band values (named Matplotlib colormaps or palettable palettes). `cmap` is a supported alias.",
        "in": "query",
        "type": "str",
    },
    "scheme": {
        "description": "This is either ``linear`` (the default) or ``discrete``. If a palette is specified, ``linear`` uses a piecewise linear interpolation, and ``discrete`` uses exact colors from the palette with the range of the data mapped into the specified number of colors (e.g., a palette with two colors will split exactly halfway between the min and max values).",
        "in": "query",
        "type": "str",
        "default": "linear",
    },
    "n_colors": {
        "description": "The number (positive integer) of colors to discretize the matplotlib color palettes when used.",
        "in": "query",
        "type": "int",
        "example": 24,
        "default": 255,
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
    "style": {
        "description": "Encoded JSON style following https://girder.github.io/large_image/tilesource_options.html#style",
        "in": "query",
        "type": "str",
    },
}
REGION_PARAMS = {
    "left": {
        "description": "The left bound (X).",
        "in": "query",
        "type": "float",
        "required": True,
    },
    "right": {
        "description": "The right bound (X).",
        "in": "query",
        "type": "float",
        "required": True,
    },
    "bottom": {
        "description": "The bottom bound (Y).",
        "in": "query",
        "type": "float",
        "required": True,
    },
    "top": {
        "description": "The top bound (Y).",
        "in": "query",
        "type": "float",
        "required": True,
    },
    "units": {
        "description": "The projection/units of the coordinates.",
        "in": "query",
        "type": "str",
        "default": "EPSG:4326",
    },
    "encoding": {
        "description": "The encoding of the output image.",
        "in": "query",
        "type": "str",
        "default": "TILED",
    },
}


def make_cache_key(*args, **kwargs):
    path = str(request.path)
    args = str(hash(frozenset(request.args.items())))
    return path + args


class ListPalettes(View):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT)
    def get(self):
        return get_palettes()


@api.doc(params=BASE_PARAMS)
class BaseImageView(View):
    def get_tile_source(self):
        """Return the built tile source."""
        try:
            filename = get_clean_filename_from_request()
        except OSError as e:
            raise BadRequest(str(e))
        try:
            return get_tile_source(filename)
        except RasterioIOError as e:
            raise BadRequest(f"RasterioIOError: {str(e)}")


class ValidateCOGView(BaseImageView):
    def get(self):
        from localtileserver.validate import validate_cog

        tile_source = self.get_tile_source()
        valid = True  # validate_cog(tile_source, strict=True)
        if valid:
            return "Valid Cloud Optimized GeoTiff."
        # TODO: better error/out?
        return "Not valid"


class MetadataView(BaseImageView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self):
        tile_source = self.get_tile_source()
        metadata = get_meta_data(tile_source)
        metadata["filename"] = str(get_clean_filename_from_request())
        return metadata


@api.doc(
    params={
        "crs": {
            "description": "The projection of the bounds.",
            "in": "query",
            "type": "str",
            "default": "EPSG:4326",
        }
    }
)
class BoundsView(BaseImageView):
    def get(self):
        tile_source = self.get_tile_source()
        bounds = get_tile_bounds(
            tile_source,
            projection=request.args.get("crs", "EPSG:4326"),
        )
        bounds["filename"] = str(get_clean_filename_from_request())
        return bounds


@api.doc(params=STYLE_PARAMS)
class ThumbnailView(BaseImageView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self, format: str = "png"):
        try:
            encoding = format_to_encoding(format)
        except ValueError:
            raise BadRequest(f"Format {format} is not a valid encoding.")
        tile_source = self.get_tile_source()
        thumb_data = tile_source.preview().render(img_format="png")
        thumb_data = io.BytesIO(thumb_data)
        return send_file(
            thumb_data,
            download_name=f"thumbnail.{format}",
            mimetype="image/png",  # TODO
        )


@api.doc(params=STYLE_PARAMS)
class BaseTileView(BaseImageView):
    @staticmethod
    def add_border_to_image(content, msg: str = None):
        img = Image.open(io.BytesIO(content))
        img = ImageOps.crop(img, 1)
        border = ImageOps.expand(img, border=1, fill="black")
        if msg is not None:
            draw = ImageDraw.Draw(border)
            w = draw.textlength(msg, direction="rtl")
            h = draw.textlength(msg, direction="ttb")
            draw.text(((255 - w) / 2, (255 - h) / 2), msg, fill="red")
        img_bytes = io.BytesIO()
        border.save(img_bytes, format="PNG")
        return img_bytes.getvalue()


@api.doc(
    params={
        "sleep": {
            "description": "The time in seconds to delay serving each tile (useful when debugging to slow things down).",
            "in": "query",
            "type": "float",
            "default": 0.5,
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
        draw = ImageDraw.Draw(img)
        msg = f"{x}/{y}/{z}"
        w = draw.textlength(msg, direction="rtl")
        h = draw.textlength(msg, direction="ttb")
        draw.text(((255 - w) / 2, (255 - h) / 2), msg, fill="black")
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
            "default": False,
        }
    }
)
class TileView(BaseTileView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self, x: int, y: int, z: int):
        tile_source = self.get_tile_source()
        try:
            tile_binary = tile_source.tile(x, y, z).render(img_format="png")
        except TileOutsideBounds as e:
            raise NotFound(str(e))
        grid = str_to_bool(request.args.get("grid", "False"))
        if grid:
            tile_binary = self.add_border_to_image(tile_binary, msg=f"{x}/{y}/{z}")
        return send_file(
            io.BytesIO(tile_binary),
            download_name=f"{x}.{y}.{z}.png",
            mimetype="image/png",
        )


@api.doc(
    params={
        "projection": {
            "description": "The projection in which to open the image (default None).",
            "in": "query",
            "type": "str",
            "default": None,
        },
    }
)
class BasePixelOperation(BaseImageView):
    pass


@api.doc(
    params={
        "x": {
            "description": "X coordinate (from left of image if in pixel space).",
            "in": "query",
            "type": "float",
            "required": True,
        },
        "y": {
            "description": "Y coordinate (from top of image if in pixel space).",
            "in": "query",
            "type": "float",
            "required": True,
        },
        "units": {
            "description": "The projection/units of the coordinates.",
            "in": "query",
            "type": "str",
            "default": "pixels",
            "example": "EPSG:4326",
        },
    }
)
class PixelView(BasePixelOperation):
    """Returns single pixel."""

    def get(self):
        projection = request.args.get("projection", None)
        x = float(request.args.get("x"))
        y = float(request.args.get("y"))
        units = request.args.get("units", "pixels")
        tile_source = self.get_tile_source(projection=projection)
        region = {"left": x, "top": y, "units": units}
        pixel = tile_source.getPixel(region=region)
        pixel.pop("value", None)
        pixel.update(region)
        return pixel
