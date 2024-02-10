import os
import pathlib
import shutil
import tempfile
from typing import Optional
from urllib.parse import urlencode, urlparse

from rasterio import CRS

from localtileserver.tiler.data import clean_url, get_data_path


class ImageBytes(bytes):
    """Wrapper class to make repr of image bytes better in ipython."""

    def __new__(cls, source: bytes, mimetype: str = None):
        self = super().__new__(cls, source)
        self._mime_type = mimetype
        return self

    @property
    def mimetype(self):
        return self._mime_type

    def _repr_png_(self):
        if self.mimetype == "image/png":
            return self

    def _repr_jpeg_(self):
        if self.mimetype == "image/jpeg":
            return self

    def __repr__(self):
        if self.mimetype:
            return f"ImageBytes<{len(self)}> ({self.mimetype})"
        return f"ImageBytes<{len(self)}> (wrapped image bytes)"


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
    """Validate encoding."""
    if not fmt:
        return "png"
    if fmt.lower() not in ["png", "jpeg", "jpg"]:
        raise ValueError(f"Format {fmt!r} is not valid. Try `png` or `jpeg`")
    if fmt.lower() == "jpg":
        fmt = "jpeg"
    return fmt.upper()  # PNG, JPEG


def make_crs(projection):
    if isinstance(projection, str):
        return CRS.from_string(projection)
    if isinstance(projection, dict):
        return CRS.from_dict(projection)
    if isinstance(projection, int):
        return CRS.from_string(f"EPSG:{projection}")
    return CRS(projection)
