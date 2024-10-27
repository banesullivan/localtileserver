import logging
import pathlib
from typing import List, Optional, Union
import warnings

from matplotlib.colors import Colormap
import rasterio

from localtileserver.client import TileClient, get_or_create_tile_client

logger = logging.getLogger(__name__)
DEFAULT_ATTRIBUTION = "Raster file served by <a href='https://github.com/banesullivan/localtileserver' target='_blank'>localtileserver</a>."


class LocalTileServerLayerMixin:
    """Mixin class for tile layers using localtileserver."""

    # Prevent the client from being garbage collected
    tile_server: TileClient


def get_leaflet_tile_layer(
    source: Union[pathlib.Path, str, TileClient, rasterio.io.DatasetReaderBase],
    port: Union[int, str] = "default",
    debug: bool = False,
    indexes: Optional[List[int]] = None,
    colormap: Optional[Union[str, Colormap, List[str]]] = None,
    vmin: Optional[Union[float, List[float]]] = None,
    vmax: Optional[Union[float, List[float]]] = None,
    nodata: Optional[Union[int, float]] = None,
    attribution: str = None,
    **kwargs,
):
    """Generate an ipyleaflet TileLayer for the given TileClient.

    Parameters
    ----------
    source : Union[pathlib.Path, str, TileClient, rasterio.io.DatasetReaderBase]
        The source of the tile layer. This can be a path on disk or an already
        open ``TileClient``
    port : int
        The port on your host machine to use for the tile server (if creating
        a tileserver. This is ignored if a file path is given). This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode (if creating a tileserver. This is
        ignored if a file path is given).
    indexes : int
        The band of the source raster to use (default if None is to show RGB if
        available). Band indexing starts at 1. This can also be a list of
        integers to set which 3 bands to use for RGB.
    colormap : str
        The name of the matplotlib colormap to use when plotting a single band.
        Default is greyscale.
    vmin : float
        The minimum value to use when colormapping a single band.
    vmax : float
        The maximized value to use when colormapping a single band.
    nodata : float
        The value from the band to use to interpret as not valid data.
    attribution : str
        Attribution for the source raster. This
        defaults to a message about it being a local file.
    **kwargs
        All additional keyword arguments are passed to ``ipyleaflet.TileLayer``.

    Return
    ------
    ipyleaflet.TileLayer

    """
    # Safely import ipyleaflet
    try:
        from ipyleaflet import TileLayer
        from traitlets import Tuple, Union
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `ipyleaflet`: {e}") from e

    if "band" in kwargs:
        indexes = kwargs.pop("band")
        warnings.warn(
            "The `band` keyword argument is deprecated. Please use `indexes` instead.",
        )
    elif "bands" in kwargs:
        indexes = kwargs.pop("bands")
        warnings.warn(
            "The `bands` keyword argument is deprecated. Please use `indexes` instead.",
        )
    if "cmap" in kwargs:
        colormap = kwargs.pop("cmap")
        warnings.warn(
            "The `cmap` keyword argument is deprecated. Please use `colormap` instead.",
        )

    class BoundTileLayer(TileLayer, LocalTileServerLayerMixin):
        # https://github.com/jupyter-widgets/ipyleaflet/issues/888
        # https://github.com/ipython/traitlets/issues/626#issuecomment-699957829
        bounds = Union((Tuple(),), default_value=None, allow_none=True).tag(sync=True, o=True)

    source, created = get_or_create_tile_client(
        source,
        port=port,
        debug=debug,
    )
    url = source.get_tile_url(
        indexes=indexes,
        colormap=colormap,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
        client=True,
    )
    if attribution is None:
        attribution = DEFAULT_ATTRIBUTION
    kwargs.setdefault("max_native_zoom", 30)  # source.max_zoom)
    kwargs.setdefault("max_zoom", 30)  # source.max_zoom)
    kwargs.setdefault("show_loading", True)
    b = source.bounds()
    bounds = ((b[0], b[2]), (b[1], b[3]))
    tile_layer = BoundTileLayer(url=url, attribution=attribution, bounds=bounds, **kwargs)
    if created:
        # HACK: Prevent the client from being garbage collected
        tile_layer.tile_server = source
    return tile_layer


def get_folium_tile_layer(
    source: Union[pathlib.Path, str, TileClient, rasterio.io.DatasetReaderBase],
    port: Union[int, str] = "default",
    debug: bool = False,
    indexes: Optional[List[int]] = None,
    colormap: Optional[str] = None,
    vmin: Optional[Union[float, List[float]]] = None,
    vmax: Optional[Union[float, List[float]]] = None,
    nodata: Optional[Union[int, float]] = None,
    attr: str = None,
    **kwargs,
):
    """Generate a folium TileLayer for the given TileClient.

    Parameters
    ----------
    source : Union[pathlib.Path, str, TileClient, rasterio.io.DatasetReaderBase]
        The source of the tile layer. This can be a path on disk or an already
        open ``TileClient``
    port : int
        The port on your host machine to use for the tile server (if creating
        a tileserver. This is ignored if a file path is given). This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode (if creating a tileserver. This is
        ignored if a file path is given).
    indexes : int
        The band of the source raster to use (default if None is to show RGB if
        available). Band indexing starts at 1. This can also be a list of
        integers to set which 3 bands to use for RGB.
    colormap : str
        The name of the matplotlib colormap to use when plotting a single band.
        Default is greyscale.
    vmin : float
        The minimum value to use when colormapping a single band.
    vmax : float
        The maximized value to use when colormapping a single band.
    nodata : float
        The value from the band to use to interpret as not valid data.
    attr : str
        Folium requires the custom tile source have an attribution. This
        defaults to a message about it being a local file.
    **kwargs
        All additional keyword arguments are passed to ``folium.TileLayer``.

    Return
    ------
    folium.TileLayer

    """
    # Safely import folium
    try:
        from folium import TileLayer
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `folium`: {e}")

    if "band" in kwargs:
        indexes = kwargs.pop("band")
        warnings.warn(
            "The `band` keyword argument is deprecated. Please use `indexes` instead.",
        )
    elif "bands" in kwargs:
        indexes = kwargs.pop("bands")
        warnings.warn(
            "The `bands` keyword argument is deprecated. Please use `indexes` instead.",
        )
    if "cmap" in kwargs:
        colormap = kwargs.pop("cmap")
        warnings.warn(
            "The `cmap` keyword argument is deprecated. Please use `colormap` instead.",
        )

    class FoliumTileLayer(TileLayer, LocalTileServerLayerMixin):
        pass

    source, created = get_or_create_tile_client(
        source,
        port=port,
        debug=debug,
    )
    url = source.get_tile_url(
        indexes=indexes,
        colormap=colormap,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
        client=True,
    )
    if attr is None:
        attr = DEFAULT_ATTRIBUTION
    b = source.bounds()
    bounds = ((b[0], b[2]), (b[1], b[3]))
    tile_layer = FoliumTileLayer(tiles=url, bounds=bounds, attr=attr, **kwargs)
    if created:
        # HACK: Prevent the client from being garbage collected
        tile_layer.tile_server = source
    return tile_layer
