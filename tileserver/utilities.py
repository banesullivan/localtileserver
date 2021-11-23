import os
import pathlib
import re
import tempfile
from operator import attrgetter

import large_image
import palettable
import requests
from furl import furl
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from osgeo import gdal


def get_cache_dir():
    path = pathlib.Path(os.path.join(tempfile.gettempdir(), "localtileserver"))
    path.mkdir(parents=True, exist_ok=True)
    return path


gdal.SetConfigOption("GDAL_ENABLE_WMS_CACHE", "YES")
gdal.SetConfigOption(
    "GDAL_DEFAULT_WMS_CACHE_PATH", str(get_cache_dir() / "gdalwmscache")
)


def save_file_from_request(response: requests.Response, output_path: pathlib.Path):
    d = response.headers["content-disposition"]
    fname = re.findall("filename=(.+)", d)[0]
    if not output_path:
        output_path = get_cache_dir() / fname
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def is_valid_palette(palette: str):
    try:
        attrgetter(palette)(palettable)
    except AttributeError:
        return False
    return True


def add_query_parameters(url: str, params: dict):
    f = furl(url)
    for k, v in params.items():
        f.args[k] = v
    return f.url


def get_tile_source(
    path: pathlib.Path, projection: str = None, style: str = None
) -> FileTileSource:
    return large_image.open(
        str(path), projection=projection, style=style, encoding="PNG"
    )


def _get_region(tile_source: FileTileSource, region: dict, encoding: str):
    result, mime_type = tile_source.getRegion(region=region, encoding=encoding)
    if encoding == "TILED":
        path = result
    else:
        # Write content to temporary file
        fd, path = tempfile.mkstemp(
            suffix=f".{encoding}", prefix="pixelRegion_", dir=str(get_cache_dir())
        )
        os.close(fd)
        path = pathlib.Path(path)
        with open(path, "wb") as f:
            f.write(result)
    return path, mime_type


def get_region_world(
    tile_source: FileTileSource,
    left: float,
    right: float,
    bottom: float,
    top: float,
    units: str = "EPSG:4326",
    encoding: str = "TILED",
):
    region = dict(left=left, right=right, bottom=bottom, top=top, units=units)
    return _get_region(tile_source, region, encoding)


def get_region_pixel(
    tile_source: FileTileSource,
    left: int,
    right: int,
    bottom: int,
    top: int,
    units: str = "pixels",
    encoding: str = None,
):
    left, right = min(left, right), max(left, right)
    top, bottom = min(top, bottom), max(top, bottom)
    region = dict(left=left, right=right, bottom=bottom, top=top, units=units)
    if isinstance(tile_source, GDALFileTileSource) and encoding is None:
        # Use tiled encoding by default for geospatial rasters
        #   output will be a tiled TIF
        encoding = "TILED"
    elif encoding is None:
        # Otherwise use JPEG encoding by default
        encoding = "JPEG"
    return _get_region(tile_source, region, encoding)


def get_tile_bounds(
    tile_source: FileTileSource,
    projection: str = "EPSG:4326",
):
    bounds = tile_source.getBounds(srs=projection)
    if projection == "EPSG:4326":
        threshold = 89.9999
        for key in ("ymin", "ymax"):
            bounds[key] = max(min(bounds[key], threshold), -threshold)
    return bounds


def get_meta_data(tile_source: FileTileSource):
    meta = tile_source.getMetadata()
    meta.update(tile_source.getInternalMetadata())
    return meta
