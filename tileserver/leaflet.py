import pathlib
from tileserver.run import TileServer
from typing import Union
import requests


def get_leaflet_tile_layer_from_tile_server(
    tile_server: TileServer,
    band: int = None,
    palette: str = None,
    vmin: Union[float, int] = None,
    vmax: Union[float, int] = None,
    nodata: Union[float, int] = None,
    **kwargs,
):
    """Generate an ipyleaflet TileLayer for the given TileServer.

    Parameters
    ----------
    **kwargs
        All additional keyword arguments are passed to TileLayer

    Return
    ------
    ipyleaflet.TileLayer

    """
    # Safely import ipyleaflet
    try:
        from ipyleaflet import TileLayer
    except ImportError:
        raise ImportError("Please install `ipyleaflet` and `jupyter`.")

    # Check that the tile source is valid and no server errors
    r = requests.get(tile_server.create_url("metadata"))
    r.raise_for_status()

    params = {}
    if band is not None:
        params["band"] = band
    if palette is not None:
        # TODO: check this value as an incorrect one can lead to server errors
        #       perhaps we should catch this, server side and ignore bad ones
        params["palette"] = palette
    if vmin is not None:
        params["min"] = vmin
    if vmax is not None:
        params["max"] = vmax
    if nodata is not None:
        params["nodata"] = nodata

    url = tile_server.create_url("tiles/{z}/{x}/{y}.png?projection=EPSG:3857")

    for k, v in params.items():
        url += f"&{k}={v}"

    return TileLayer(url=url, **kwargs)


def get_leaflet_tile_layer(
    source: Union[pathlib.Path, TileServer],
    port: int = 0,
    debug: bool = False,
    **kwargs,
):
    if not isinstance(source, TileServer):
        source = TileServer(source, port, debug)
    return get_leaflet_tile_layer_from_tile_server(source, **kwargs)
