import io

from flask import request, send_file
from flask_restx import Api, Resource as View
from rasterio import RasterioIOError
from rio_tiler.errors import TileOutsideBounds
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType

from localtileserver import __version__
from localtileserver.tiler import (
    format_to_encoding,
    get_meta_data,
    get_preview,
    get_reader,
    get_source_bounds,
    get_tile,
)
from localtileserver.tiler.palettes import get_palettes
from localtileserver.web.blueprint import cache, tileserver
from localtileserver.web.utils import (
    get_clean_filename_from_request,
    reformat_list_query_parameters,
)

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
        "example": "https://localtileserver.s3.us-west-2.amazonaws.com/examples/TC_NG_SFBay_US_Geo.tif",
    },
}
STYLE_PARAMS = {
    "indexes": {
        "description": "The band number(s) to use.",
        "in": "query",
        "type": "int",  # TODO: make this a list
    },
    "colormap": {
        "description": "The color palette to map the band values (named Matplotlib colormaps). `cmap` is a supported alias.",
        "in": "query",
        "type": "str",
    },
    "vmin": {
        "description": "The minimum value for the color mapping.",
        "in": "query",
        "type": "float",
    },
    "vmax": {
        "description": "The maximum value for the color mapping.",
        "in": "query",
        "type": "float",
    },
    "nodata": {
        "description": "The value to map as no data (often made transparent). Defaults to NaN.",
        "in": "query",
        "type": "float",
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
    def get_reader(self):
        """Return the built tile source."""
        try:
            filename = get_clean_filename_from_request()
        except OSError as e:
            raise BadRequest(str(e)) from e
        try:
            return get_reader(filename)
        except RasterioIOError as e:
            raise BadRequest(f"RasterioIOError: {str(e)}") from e

    def get_clean_args(self):
        return {
            k: v
            for k, v in reformat_list_query_parameters(request.args).items()
            if k in STYLE_PARAMS
        }


class ValidateCOGView(BaseImageView):
    def get(self):
        from localtileserver.validate import validate_cog

        tile_source = self.get_reader()
        valid = validate_cog(tile_source, strict=True)
        if not valid:
            raise UnsupportedMediaType("Not a valid Cloud Optimized GeoTiff.")
        return "Valid Cloud Optimized GeoTiff."


class MetadataView(BaseImageView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self):
        tile_source = self.get_reader()
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
        tile_source = self.get_reader()
        bounds = get_source_bounds(
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
        except ValueError as e:
            raise BadRequest(f"Format {format} is not a valid encoding.") from e
        tile_source = self.get_reader()
        thumb_data = get_preview(tile_source, img_format=encoding, **self.get_clean_args())
        thumb_data = io.BytesIO(thumb_data)
        return send_file(
            thumb_data,
            download_name=f"thumbnail.{format}",
            mimetype=f"image/{format.lower()}",
        )


@api.doc(params=STYLE_PARAMS)
class TileView(BaseImageView):
    @cache.cached(timeout=REQUEST_CACHE_TIMEOUT, key_prefix=make_cache_key)
    def get(self, x: int, y: int, z: int, format: str = "png"):
        tile_source = self.get_reader()
        img_format = format_to_encoding(format)
        try:
            tile_binary = get_tile(
                tile_source, z, x, y, img_format=img_format, **self.get_clean_args()
            )
        except TileOutsideBounds as e:
            raise NotFound(str(e)) from e
        return send_file(
            io.BytesIO(tile_binary),
            download_name=f"{x}.{y}.{z}.png",
            mimetype=f"image/{img_format}",
        )
