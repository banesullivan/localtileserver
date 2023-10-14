import logging
import os
import pathlib
import shutil
import tempfile
from typing import Optional
from urllib.parse import urlencode, urlparse

from rasterio import CRS

from localtileserver.tiler.data import clean_url, get_data_path, get_pine_gulch_url

logger = logging.getLogger(__name__)


def get_cache_dir():
    path = pathlib.Path(os.path.join(tempfile.gettempdir(), "localtileserver"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def purge_cache():
    """Completely purge all files from the file cache.

    This should be used with caution, it could delete files that are in use.
    """
    cache = get_cache_dir()
    shutil.rmtree(cache)
    # Return the cache dir so that a fresh directory is created.
    return get_cache_dir()


def make_vsi(url: str, **options):
    url = clean_url(url)
    if str(url).startswith("s3://"):
        s3_path = url.replace("s3://", "")
        vsi = f"/vsis3/{s3_path}"
    else:
        uoptions = {
            "url": str(url),
            "use_head": "no",
            "list_dir": "no",
        }
        uoptions.update(options)
        vsi = f"/vsicurl?{urlencode(uoptions)}"
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


def format_to_encoding(fmt: Optional[str]) -> str:
    """Translate format extension (e.g., `tiff`) to encoding (e.g., `TILED`)."""
    if not fmt:
        return "PNG"
    if fmt.lower() not in ["tif", "tiff", "png", "jpeg", "jpg"]:
        raise ValueError(f"Format {fmt!r} is not valid. Try `png`, `jpeg`, or `tif`")
    if fmt.lower() in ["tif", "tiff"]:
        return "TILED"
    if fmt.lower() == "jpg":
        fmt = "jpeg"
    return fmt.upper()  # jpeg, png


def make_crs(projection):
    if isinstance(projection, str):
        return CRS.from_string(projection)
    if isinstance(projection, dict):
        return CRS.from_dict(projection)
    if isinstance(projection, int):
        return CRS.from_string(f"EPSG:{projection}")
    return CRS(projection)
