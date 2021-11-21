import pathlib
from tileserver.run import TileServer
from typing import Union
import requests

from tileserver.utilities import is_valid_palette


def get_leaflet_tile_layer(
    source: Union[pathlib.Path, TileServer],
    port: int = 0,
    debug: bool = False,
    projection: str = "EPSG:3857",
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

    # First handle query parameters to check for errors
    params = {}
    if band is not None:
        params["band"] = band
    if palette is not None:
        if not is_valid_palette(palette):
            raise ValueError(
                f"Palette choice of {palette} is invalid. Check available palettes in the `palettable` package."
            )
        params["palette"] = palette
    if vmin is not None:
        params["min"] = vmin
    if vmax is not None:
        params["max"] = vmax
    if nodata is not None:
        params["nodata"] = nodata

    # Launch tile server if file path is given
    if not isinstance(source, TileServer):
        source = TileServer(source, port, debug)

    # Check that the tile source is valid and no server errors
    r = requests.get(source.create_url("metadata"))
    r.raise_for_status()

    url = source.get_tile_url(projection=projection)
    for k, v in params.items():
        url += f"&{k}={v}"

    return TileLayer(url=url, **kwargs)
