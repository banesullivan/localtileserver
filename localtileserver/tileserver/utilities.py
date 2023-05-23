import logging
import os
import pathlib
import shutil
import tempfile
from typing import Optional, Union
from urllib.parse import urlencode, urlparse

from flask import current_app, request
import large_image
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from osgeo import gdal

from localtileserver.tileserver.data import (
    clean_url,
    get_data_path,
    get_pine_gulch_url,
    get_sf_bay_url,
)

logger = logging.getLogger(__name__)


def get_memcache_config():
    url, username, password = None, None, None
    if os.environ.get("MEMCACHED_URL", ""):
        url = os.environ.get("MEMCACHED_URL")
        if os.environ.get("MEMCACHED_USERNAME", "") and os.environ.get("MEMCACHED_PASSWORD", ""):
            username = os.environ.get("MEMCACHED_USERNAME")
            password = os.environ.get("MEMCACHED_PASSWORD")
    elif os.environ.get("MEMCACHIER_SERVERS", ""):
        url = os.environ.get("MEMCACHIER_SERVERS")
        if os.environ.get("MEMCACHIER_USERNAME", "") and os.environ.get("MEMCACHIER_PASSWORD", ""):
            username = os.environ.get("MEMCACHIER_USERNAME")
            password = os.environ.get("MEMCACHIER_PASSWORD")
    return url, username, password


def configure_large_image_memcache(url: str, username: str = None, password: str = None):
    if url:
        large_image.config.setConfig("cache_memcached_url", url)
        if username and password:
            large_image.config.setConfig("cache_memcached_username", username)
            large_image.config.setConfig("cache_memcached_password", password)
        large_image.config.setConfig("cache_backend", "memcached")
        logger.info("large_image is configured for memcached.")


def get_cache_dir():
    path = pathlib.Path(os.path.join(tempfile.gettempdir(), "localtileserver"))
    path.mkdir(parents=True, exist_ok=True)
    return path


configure_large_image_memcache(*get_memcache_config())
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


def is_geospatial(source: FileTileSource) -> bool:
    return source.getMetadata().get("geospatial", False)


def get_tile_source(
    path: Union[pathlib.Path, str], projection: str = None, style: str = None, encoding: str = "PNG"
) -> FileTileSource:
    return large_image.open(str(path), projection=projection, style=style, encoding=encoding)


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
    if not is_geospatial(tile_source):
        return {"xmin": 0, "xmax": tile_source.sizeX, "ymin": 0, "ymax": tile_source.sizeY}
    bounds = tile_source.getBounds(srs=projection)
    if projection == "EPSG:4326":
        threshold = 89.9999
        for key in ("ymin", "ymax"):
            bounds[key] = max(min(bounds[key], threshold), -threshold)
    return bounds


def get_meta_data(tile_source: FileTileSource):
    meta = tile_source.getMetadata()
    meta.update(tile_source.getInternalMetadata())
    # Override bounds for EPSG:4326
    meta["bounds"] = get_tile_bounds(tile_source)
    return meta


def make_vsi(url: str, **options):
    url = clean_url(url)
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
    if not filename:
        raise OSError("Empty path given")  # pragma: no cover

    # Check for example first
    if filename == "blue_marble":
        filename = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    elif filename == "virtual_earth":
        filename = get_data_path("frmt_wms_virtualearth.xml")
    elif filename == "arcgis":
        filename = get_data_path("frmt_wms_arcgis_mapserver_tms.xml")
    elif filename in ["elevation", "dem", "topo"]:
        filename = get_data_path("aws_elevation_tiles_prod.xml")
    elif filename == "bahamas":
        filename = get_data_path("bahamas_rgb.tif")
    elif filename == "pine_gulch":
        filename = get_pine_gulch_url()

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


def get_clean_filename_from_request(param_name: str = "filename", strict: bool = False):
    try:
        # First look for filename in URL params
        f = request.args.get(param_name)
        if not f:
            raise KeyError
        filename = get_clean_filename(f)
    except KeyError:
        # Backup to app.config
        try:
            filename = get_clean_filename(current_app.config[param_name])
        except KeyError:
            message = "No filename set in app config or URL params. Using sample data."
            if strict:
                raise OSError(message)
            # Fallback to sample data
            logger.error(message)
            filename = get_clean_filename(get_sf_bay_url())
    return filename


def format_to_encoding(format: Optional[str]) -> str:
    """Translate format extension (e.g., `tiff`) to encoding (e.g., `TILED`)."""
    if not format:
        return "PNG"
    if format.lower() not in ["tif", "tiff", "png", "jpeg", "jpg"]:
        raise ValueError(f"Format {format!r} is not valid. Try `png`, `jpeg`, or `tif`")
    if format.lower() in ["tif", "tiff"]:
        return "TILED"
    if format.lower() == "jpg":
        format = "jpeg"
    return format.upper()  # jpeg, png
