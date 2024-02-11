from functools import wraps
from typing import Union

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
    port: Union[int, str] = "default",
    debug: bool = False,
    client_port: int = None,
    client_host: str = None,
    client_prefix: str = None,
):
    raise NotImplementedError  # pragma: no cover


@wraps(_get_example_client)
def get_blue_marble(*args, **kwargs):
    path = get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_virtual_earth(*args, **kwargs):
    path = get_data_path("frmt_wms_virtualearth.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_arcgis(*args, **kwargs):
    path = get_data_path("frmt_wms_arcgis_mapserver_tms.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_elevation(*args, **kwargs):
    path = get_data_path("aws_elevation_tiles_prod.xml")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_bahamas(*args, **kwargs):
    path = get_data_path("bahamas_rgb.tif")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_landsat(*args, **kwargs):
    path = get_data_path("landsat.tif")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_landsat7(*args, **kwargs):
    path = get_data_path("landsat7.tif")
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_san_francisco(*args, **kwargs):
    path = get_sf_bay_url()
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_oam2(*args, **kwargs):
    path = get_oam2_url()
    return TileClient(path, *args, **kwargs)


@wraps(_get_example_client)
def get_elevation_us(*args, **kwargs):
    path = get_elevation_us_url()
    return TileClient(path, *args, **kwargs)


def load_presidio():
    """Load Presidio of San Francisco boundary as Shapely Polygon."""
    with open(DIRECTORY / "presidio.wkb", "rb") as f:
        return parse_shapely(f.read())


@wraps(_get_example_client)
def get_co_elevation(*args, local_roi=False, **kwargs):
    if local_roi:
        path = get_data_path("co_elevation_roi.tif")
    else:
        path = get_co_elevation_url()
    return TileClient(path, *args, **kwargs)
