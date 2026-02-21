"""
Utility functions for path resolution, caching, and CRS handling.
"""

import os
import pathlib
import shutil
import tempfile
from urllib.parse import urlencode, urlparse

from rasterio import CRS

from localtileserver.tiler.data import clean_url, get_data_path


class ImageBytes(bytes):
    """
    Wrapper around bytes for improved image representation in IPython.

    Accepts ``source`` (raw image bytes) and an optional ``mimetype``
    (e.g., ``"image/png"``) to enable rich display in Jupyter notebooks.
    """

    def __new__(cls, source: bytes, mimetype: str | None = None):
        self = super().__new__(cls, source)
        self._mime_type = mimetype
        return self

    @property
    def mimetype(self):
        """
        Return the MIME type of the image.

        Returns
        -------
        str or None
            The MIME type string, or ``None`` if not set.
        """
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
    """
    Return the localtileserver cache directory, creating it if needed.

    Returns
    -------
    pathlib.Path
        Path to the cache directory under the system temporary directory.
    """
    path = pathlib.Path(os.path.join(tempfile.gettempdir(), "localtileserver"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def purge_cache():
    """
    Completely purge all files from the file cache.

    This should be used with caution, it could delete files that are in use.

    Returns
    -------
    pathlib.Path
        Path to the newly created, empty cache directory.
    """
    cache = get_cache_dir()
    shutil.rmtree(cache)
    # Return the cache dir so that a fresh directory is created.
    return get_cache_dir()


def make_vsi(url: str, **options):
    """
    Build a GDAL virtual filesystem (VSI) path from a URL.

    S3 URLs are converted to ``/vsis3/`` paths; all other URLs are
    converted to ``/vsicurl?`` paths with sensible defaults.

    Parameters
    ----------
    url : str
        The source URL (``http://``, ``https://``, or ``s3://``).
    **options : dict
        Additional key-value pairs appended to the ``/vsicurl`` query
        string.  Ignored for S3 URLs.

    Returns
    -------
    str
        A GDAL-compatible VSI path string.
    """
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
    """
    Resolve a filename to a local path or GDAL virtual filesystem path.

    Built-in example dataset names (e.g., ``"blue_marble"``,
    ``"bahamas"``) are expanded to their bundled data paths.  Remote
    URLs are converted to GDAL VSI paths, and local paths are resolved
    to absolute ``pathlib.Path`` objects.

    Parameters
    ----------
    filename : str
        A local file path, a remote URL, a GDAL driver prefix string,
        or a built-in example dataset name.

    Returns
    -------
    str or pathlib.Path
        A GDAL-compatible VSI string for remote sources and GDAL driver
        prefixes, or an absolute ``pathlib.Path`` for local files.

    Raises
    ------
    OSError
        If *filename* is empty or the resolved local path does not exist.
    """
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
    # GDAL driver connection prefixes (e.g., GTI:/path/to/file.gpkg) use a
    # colon that urlparse misinterprets as a URL scheme. Pass these through
    # directly — rasterio/GDAL handles them natively.
    _GDAL_PREFIXES = ("GTI:", "WMTS:", "DAAS:", "EEDAI:", "NGW:", "PLMOSAIC:", "PLSCENES:")
    if str(filename).startswith(_GDAL_PREFIXES):
        return str(filename)
    parsed = urlparse(str(filename))
    if parsed.scheme in ["http", "https", "s3"]:
        return make_vsi(filename)
    # Otherwise, treat as local path on Disk
    filename = pathlib.Path(filename).expanduser().absolute()
    if not filename.exists():
        raise OSError(f"Path does not exist: {filename}")
    return filename


_FORMAT_MAP = {
    "png": "PNG",
    "jpeg": "JPEG",
    "jpg": "JPEG",
    "webp": "WEBP",
    "tif": "GTiff",
    "tiff": "GTiff",
    "geotiff": "GTiff",
    "npy": "NPY",
}


def format_to_encoding(fmt: str | None) -> str:
    """
    Validate encoding and return the canonical GDAL format string.

    Supported formats: png, jpeg/jpg, webp, tif/tiff/geotiff, npy.

    Parameters
    ----------
    fmt : str or None
        A short format name (case-insensitive).  If ``None`` or empty,
        defaults to ``"png"``.

    Returns
    -------
    str
        The canonical GDAL driver name (e.g., ``"PNG"``, ``"JPEG"``,
        ``"GTiff"``).

    Raises
    ------
    ValueError
        If *fmt* is not a recognised format name.
    """
    if not fmt:
        return "png"
    encoding = _FORMAT_MAP.get(fmt.lower())
    if encoding is None:
        valid = ", ".join(sorted(set(_FORMAT_MAP.values())))
        raise ValueError(f"Format {fmt!r} is not valid. Supported formats: {valid}")
    return encoding


def make_crs(projection):
    """
    Create a ``rasterio.CRS`` from various projection representations.

    Parameters
    ----------
    projection : str, dict, or int
        A CRS specification.  Strings are parsed via
        ``CRS.from_string``, dicts via ``CRS.from_dict``, integers are
        treated as EPSG codes, and any other type is passed directly to
        the ``CRS`` constructor.

    Returns
    -------
    rasterio.CRS
        The corresponding coordinate reference system object.
    """
    if isinstance(projection, str):
        return CRS.from_string(projection)
    if isinstance(projection, dict):
        return CRS.from_dict(projection)
    if isinstance(projection, int):
        return CRS.from_string(f"EPSG:{projection}")
    return CRS(projection)
