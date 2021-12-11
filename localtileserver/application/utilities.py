import os
import pathlib
import shutil
import tempfile
from typing import Union
from urllib.parse import urlencode, urlparse

import large_image
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from osgeo import gdal


def get_cache_dir():
    path = pathlib.Path(os.path.join(tempfile.gettempdir(), "localtileserver"))
    path.mkdir(parents=True, exist_ok=True)
    return path


gdal.SetConfigOption("GDAL_ENABLE_WMS_CACHE", "YES")
gdal.SetConfigOption("GDAL_DEFAULT_WMS_CACHE_PATH", str(get_cache_dir() / "gdalwmscache"))


def purge_cache():
    """Completely purge all files from the file cache.

    This should be used with caution, it could delete files that are in use.
    """
    cache = get_cache_dir()
    shutil.rmtree(cache)
    # Return the cache dir so that a fresh directory is created.
    return get_cache_dir()


def get_tile_source(
    path: Union[pathlib.Path, str], projection: str = None, style: str = None
) -> FileTileSource:
    return large_image.open(str(path), projection=projection, style=style, encoding="PNG")


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


def make_vsi(url: str, **options):
    if str(url).startswith("s3://"):
        s3_path = url.replace("s3://", "")
        vsi = f"/vsis3/{s3_path}"
    else:
        gdal_options = {
            "url": str(url),
            "use_head": "no",
            "list_dir": "no",
        }
        gdal_options.update(options)
        vsi = f"/vsicurl?{urlencode(gdal_options)}"
    return vsi


def get_clean_filename(filename: str):
    if str(filename).startswith("/vsi"):
        return filename
    parsed = urlparse(str(filename))
    if parsed.scheme in ["http", "https", "s3"]:
        return make_vsi(filename)
    # Otherwise, treat as local path on Disk
    filename = pathlib.Path(filename).expanduser().absolute()
    if not filename.exists():
        raise OSError(f"Path does not exist: {filename}")
    return filename
