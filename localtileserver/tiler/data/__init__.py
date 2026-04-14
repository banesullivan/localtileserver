"""
Bundled example data files and URL helpers.
"""

import os
import pathlib

DIRECTORY = pathlib.Path(__file__).parent


def str_to_bool(v):
    """
    Convert a string representation of a truth value to a boolean.

    Parameters
    ----------
    v : str
        A string to evaluate as a boolean. Case-insensitive values of
        ``"yes"``, ``"true"``, ``"t"``, ``"1"``, ``"on"``, and ``"y"``
        are considered ``True``.

    Returns
    -------
    bool
        ``True`` if `v` matches a truthy string, ``False`` otherwise.
    """
    return v.lower() in ("yes", "true", "t", "1", "on", "y")


def get_building_docs():
    """
    Check whether the documentation build environment is active.

    Inspects the ``LOCALTILESERVER_BUILDING_DOCS`` environment variable
    to determine if the package is currently being used during a
    documentation build.

    Returns
    -------
    bool
        ``True`` if the ``LOCALTILESERVER_BUILDING_DOCS`` environment
        variable is set to a truthy value, ``False`` otherwise.
    """
    if "LOCALTILESERVER_BUILDING_DOCS" in os.environ and str_to_bool(
        os.environ["LOCALTILESERVER_BUILDING_DOCS"]
    ):
        return True
    return False


def get_data_path(name):
    """
    Return the path or URL to a bundled data file.

    When building documentation, a remote GitHub URL is returned so that
    the data files do not need to be present locally. Otherwise, the
    local filesystem path is returned.

    Parameters
    ----------
    name : str
        The filename of the data file (e.g., ``"dem.tif"``).

    Returns
    -------
    pathlib.Path or str
        A ``pathlib.Path`` to the local file when running normally, or a
        ``str`` URL pointing to the file on GitHub when building docs.
    """
    if get_building_docs():
        return f"https://github.com/banesullivan/localtileserver/raw/main/localtileserver/tiler/data/{name}"
    else:
        return DIRECTORY / name


def get_sf_bay_url():
    """
    Return the URL for the San Francisco Bay area sample raster.

    Returns
    -------
    str
        URL to a Cloud-Optimized GeoTIFF of the San Francisco Bay area.
    """
    return "https://pub-5ec9af56ea924492b07db6cf4015bba0.r2.dev/examples/TC_NG_SFBay_US_Geo_COG.tif"


def get_elevation_us_url():
    """
    Return the URL for the US elevation sample raster.

    Returns
    -------
    str
        URL to a Cloud-Optimized GeoTIFF of US elevation data.
    """
    return "https://pub-5ec9af56ea924492b07db6cf4015bba0.r2.dev/examples/elevation_cog.tif"


def get_oam2_url():
    """
    Return the URL for the OpenAerialMap sample raster.

    Returns
    -------
    str
        URL to a Cloud-Optimized GeoTIFF from OpenAerialMap.
    """
    return "https://pub-5ec9af56ea924492b07db6cf4015bba0.r2.dev/examples/oam2.tif"


def convert_dropbox_url(url: str):
    """
    Convert a Dropbox sharing URL to a direct download URL.

    Replaces the ``www.dropbox.com`` host with ``dl.dropbox.com`` so
    that the file can be downloaded directly without the Dropbox web
    interface.

    Parameters
    ----------
    url : str
        A Dropbox URL (e.g.,
        ``"https://www.dropbox.com/s/abc123/file.tif"``).

    Returns
    -------
    str
        The URL with the host replaced for direct download. If the URL
        is not a Dropbox URL, it is returned unchanged.
    """
    return url.replace("https://www.dropbox.com", "https://dl.dropbox.com")


def clean_url(url: str):
    """
    Fix the download URL for common hosting services like Dropbox.

    Applies host-specific URL transformations so that the returned URL
    points directly to the downloadable resource.

    Parameters
    ----------
    url : str
        A URL that may require transformation for direct access.

    Returns
    -------
    str
        The cleaned URL suitable for direct download.
    """
    return convert_dropbox_url(url)


def get_co_elevation_url():
    """
    Return the URL for the Colorado elevation sample raster.

    Returns
    -------
    str
        URL to a Cloud-Optimized GeoTIFF of Colorado elevation data.
    """
    return "https://pub-5ec9af56ea924492b07db6cf4015bba0.r2.dev/examples/co_elevation_roi.tif"


def get_landsat_vegas_b30_url():
    """
    Return the URL for the Landsat Vegas Band 30 sample raster.

    Returns
    -------
    str
        URL to a Landsat 5 Band 30 GeoTIFF over Las Vegas.
    """
    return "https://pub-5ec9af56ea924492b07db6cf4015bba0.r2.dev/examples/landsat_vegas/L5039035_03520060512_B30.TIF"


def get_landsat_vegas_b70_url():
    """
    Return the URL for the Landsat Vegas Band 70 sample raster.

    Returns
    -------
    str
        URL to a Landsat 5 Band 70 GeoTIFF over Las Vegas.
    """
    return "https://pub-5ec9af56ea924492b07db6cf4015bba0.r2.dev/examples/landsat_vegas/L5039035_03520060512_B70.TIF"
