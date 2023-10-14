"""Methods for working with images."""
from contextlib import contextmanager
import logging
import os
import pathlib
import tempfile
from typing import Union

import rasterio
from rio_tiler.io import Reader

from .utilities import get_cache_dir, get_clean_filename, make_crs

logger = logging.getLogger(__name__)


# gdal.SetConfigOption("GDAL_ENABLE_WMS_CACHE", "YES")
# gdal.SetConfigOption("GDAL_DEFAULT_WMS_CACHE_PATH", str(get_cache_dir() / "gdalwmscache"))
# TODO: what's the other option for directories on S3?
# TODO: should I set these in a rasterio.Env?


def get_tile_source(path: Union[pathlib.Path, str]) -> Reader:
    return Reader(get_clean_filename(path))


@contextmanager
def yield_tile_source(path: Union[pathlib.Path, str]) -> Reader:
    with get_tile_source(path) as source:
        yield source


def get_meta_data(tile_source: Reader):
    metadata = tile_source.dataset.meta
    metadata.update(crs=metadata["crs"].to_wkt(), transform=list(metadata["transform"]))
    return metadata


def _get_region(tile_source: Reader, region: dict, encoding: str):
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
    tile_source: Reader,
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
    tile_source: Reader,
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
    if encoding is None:
        # Use tiled encoding by default for geospatial rasters
        #   output will be a tiled TIF
        encoding = "TILED"
    return _get_region(tile_source, region, encoding)


def get_tile_bounds(
    tile_source: Reader,
    projection: str = "EPSG:4326",
    decimal_places : int = 6
):
    src_crs = tile_source.dataset.crs
    dst_crs = make_crs(projection)
    left, bottom, right, top = rasterio.warp.transform_bounds(
        src_crs, dst_crs, *tile_source.dataset.bounds
    )
    return {
        "left": round(left, decimal_places),
        "bottom": round(bottom, decimal_places),
        "right:": round(right, decimal_places),
        "top": round(top, decimal_places),
        # west, south, east, north
        "west": round(left, decimal_places),
        "south": round(bottom, decimal_places),
        "east": round(right, decimal_places),
        "north": round(top, decimal_places),
    }
