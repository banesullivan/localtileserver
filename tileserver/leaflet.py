import pathlib
from typing import Union

import requests

from tileserver.server import TileClient
from tileserver.utilities import is_valid_palette


def get_leaflet_tile_layer(
    source: Union[pathlib.Path, TileClient],
    port: Union[int, str] = "default",
    debug: bool = False,
    projection: str = "EPSG:3857",
    band: int = None,
    palette: str = None,
    vmin: Union[float, int] = None,
    vmax: Union[float, int] = None,
    nodata: Union[float, int] = None,
    **kwargs,
):
    """Generate an ipyleaflet TileLayer for the given TileClient.

    Parameters
    ----------
    source : Union[pathlib.Path, TileClient]
        The source of the tile layer. This can be a path on disk or an already
        open ``TileClient``
    port : int
        The port on your host machine to use for the tile server (if creating
        a tileserver. This is ignored if a file path is given). This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode (if creating a tileserver. This is
        ignored if a file path is given).
    projection : str
        The Proj projection to use for the tile layer. Default is `EPSG:3857`.
    band : int
        The band of the source raster to use (default in None to show RGB if
        available). Band indexing starts at 1.
    palette : str
        The name of the color palette from `palettable` to use when plotting
        a single band. Default is greyscale.
    vmin : float
        The minimum value to use when colormapping the palette when plotting
        a single band.
    vmax : float
        The maximized value to use when colormapping the palette when plotting
        a single band.
    nodata : float
        The value from the band to use to interpret as not valid data.
    **kwargs
        All additional keyword arguments are passed to ``ipyleaflet.TileLayer``.

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

    _internally_created = False
    # Launch tile server if file path is given
    if not isinstance(source, TileClient):
        source = TileClient(source, port, debug)
        _internally_created = True

    # Check that the tile source is valid and no server errors
    try:
        r = requests.get(source.create_url("metadata"))
        r.raise_for_status()
    except requests.HTTPError as e:
        # Make sure to destroy the server and its thread if internally created.
        if _internally_created:
            source.shutdown()
            del source
        raise e

    url = source.get_tile_url(projection=projection)
    for k, v in params.items():
        url += f"&{k}={v}"

    tile_layer = TileLayer(url=url, **kwargs)
    if _internally_created:
        # HACK: Prevent the server from being garbage collected
        tile_layer.tile_server = source
    return tile_layer
