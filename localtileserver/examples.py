"""
Example dataset loaders for localtileserver.
"""

from functools import wraps

from localtileserver.client import TileClient
from localtileserver.helpers import parse_shapely
from localtileserver.tiler import (
    get_co_elevation_url,
    get_data_path,
    get_elevation_us_url,
    get_oam2_url,
    get_sf_bay_url,
)
from localtileserver.tiler.data import DIRECTORY


def _get_example_client(
    port: int | str = "default",
    debug: bool = False,
    client_port: int | None = None,
    client_host: str | None = None,
    client_prefix: str | None = None,
):
    """
    Template signature for example TileClient factory functions.

    Parameters
    ----------
    port : int or str, optional
        The port on which to serve tiles. Default is ``"default"``.
    debug : bool, optional
        Whether to enable debug mode. Default is ``False``.
    client_port : int or None, optional
        The port for the client to connect to.
    client_host : str or None, optional
        The host for the client to connect to.
    client_prefix : str or None, optional
        The URL prefix for the client.
    """
    raise NotImplementedError  # pragma: no cover


@wraps(_get_example_client)
def get_blue_marble(*args, **kwargs):
    """
    Load NASA Blue Marble imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving Blue Marble imagery.
    """
    path = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_virtual_earth(*args, **kwargs):
    """
    Load Microsoft Virtual Earth imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving Virtual Earth imagery.
    """
    path = get_data_path("frmt_wms_virtualearth.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_arcgis(*args, **kwargs):
    """
    Load ArcGIS MapServer imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving ArcGIS MapServer imagery.
    """
    path = get_data_path("frmt_wms_arcgis_mapserver_tms.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_elevation(*args, **kwargs):
    """
    Load AWS elevation tiles as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving AWS elevation tile data.
    """
    path = get_data_path("aws_elevation_tiles_prod.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_bahamas(*args, **kwargs):
    """
    Load Bahamas RGB satellite imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving Bahamas RGB imagery.
    """
    path = get_data_path("bahamas_rgb.tif")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_landsat(*args, **kwargs):
    """
    Load Landsat satellite imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving Landsat imagery.
    """
    path = get_data_path("landsat.tif")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_landsat7(*args, **kwargs):
    """
    Load Landsat 7 satellite imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving Landsat 7 imagery.
    """
    path = get_data_path("landsat7.tif")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_san_francisco(*args, **kwargs):
    """
    Load San Francisco Bay area imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving San Francisco Bay area imagery.
    """
    path = get_sf_bay_url()
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_oam2(*args, **kwargs):
    """
    Load OpenAerialMap imagery as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving OpenAerialMap imagery.
    """
    path = get_oam2_url()
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_elevation_us(*args, **kwargs):
    """
    Load US elevation data as a TileClient.

    Returns
    -------
    TileClient
        A tile client serving US elevation data.
    """
    path = get_elevation_us_url()
    return TileClient(path, *args, **kwargs)


def load_presidio():
    """
    Load Presidio of San Francisco boundary as a Shapely Polygon.

    Returns
    -------
    shapely.geometry.BaseGeometry
        The Presidio boundary polygon.
    """
    with open(DIRECTORY / "presidio.wkb", "rb") as f:
        return parse_shapely(f.read())


@wraps(_get_example_client)
def get_co_elevation(*args, local_roi=False, **kwargs):
    """
    Load Colorado elevation data as a TileClient.

    Parameters
    ----------
    local_roi : bool, optional
        If ``True``, use a local region-of-interest subset of the elevation
        data. Default is ``False``.

    Returns
    -------
    TileClient
        A tile client serving Colorado elevation data.
    """
    if local_roi:
        path = get_data_path("co_elevation_roi.tif")
    else:
        path = get_co_elevation_url()
    return TileClient(path, *args, **kwargs)
