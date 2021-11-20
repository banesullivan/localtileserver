from contextlib import contextmanager
import os
import pathlib
import tempfile

import large_image
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource

from tileserver.utilities import get_cache_dir


def get_tilesource(
    path: pathlib.Path, projection: str = None, style: str = None
) -> FileTileSource:
    return large_image.open(
        str(path), projection=projection, style=style, encoding="PNG"
    )


@contextmanager
def yeild_tilesource(path: pathlib.Path, projection: str = None) -> FileTileSource:
    tile_source = get_tilesource(path, projection)
    yield tile_source
    tile_source = None


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
    threshold = 89.9999
    for key in ("ymin", "ymax"):
        bounds[key] = max(min(bounds[key], threshold), -threshold)
    return bounds


def get_meta_data(tile_source: FileTileSource):
    meta = tile_source.getMetadata()
    meta.update(tile_source.getInternalMetadata())
    return meta
