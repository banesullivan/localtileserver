"""
Jupyter widget helpers for ipyleaflet and folium tile layers.
"""

import logging
import pathlib
import warnings

from matplotlib.colors import Colormap
import rasterio

from localtileserver.client import TileClient, get_or_create_tile_client

logger = logging.getLogger(__name__)


def _is_colab():
    """
    Check if running in Google Colab.
    """
    try:
        import google.colab  # noqa: F401

        return True
    except ImportError:
        return False


def _get_colab_proxy_url(port: int) -> str | None:
    """
    Get Colab's proxy URL for a given port.

    Returns the proxy URL string, or None if not in Colab or eval_js fails.
    """
    try:
        from google.colab.output import eval_js

        url = eval_js(f"google.colab.kernel.proxyPort({port})")
        if url:
            return str(url).rstrip("/")
    except Exception:
        pass
    return None


DEFAULT_ATTRIBUTION = (
    "Raster file served by <a href='https://github.com/banesullivan/localtileserver'"
    " target='_blank'>localtileserver</a>."
)


class LocalTileServerLayerMixin:
    """
    Mixin class for tile layers using localtileserver.
    """

    # Prevent the client from being garbage collected
    tile_server: TileClient


def get_leaflet_tile_layer(
    source: pathlib.Path | str | TileClient | rasterio.io.DatasetReaderBase,
    port: int | str = "default",
    debug: bool = False,
    indexes: list[int] | None = None,
    colormap: str | Colormap | list[str] | None = None,
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
    nodata: int | float | None = None,
    attribution: str | None = None,
    **kwargs,
):
    """
    Generate an ipyleaflet TileLayer for the given TileClient.

    Parameters
    ----------
    source : pathlib.Path or str or TileClient or rasterio.io.DatasetReaderBase
        The source of the tile layer. This can be a path on disk or an already
        open ``TileClient``.
    port : int or str, optional
        The port on your host machine to use for the tile server (if creating
        a tileserver). This is ignored if a ``TileClient`` is given. This
        defaults to getting an available port.
    debug : bool, optional
        Run the tile server in debug mode (if creating a tileserver). This is
        ignored if a ``TileClient`` is given.
    indexes : list of int, optional
        The band of the source raster to use (default if ``None`` is to show
        RGB if available). Band indexing starts at 1. This can also be a list
        of integers to set which 3 bands to use for RGB.
    colormap : str or matplotlib.colors.Colormap or list of str, optional
        The name of the matplotlib colormap to use when plotting a single band.
        Default is greyscale.
    vmin : float or list of float, optional
        The minimum value to use when colormapping a single band.
    vmax : float or list of float, optional
        The maximum value to use when colormapping a single band.
    nodata : int or float, optional
        The value from the band to use to interpret as not valid data.
    attribution : str, optional
        Attribution for the source raster. This defaults to a message about
        it being a local file.
    **kwargs
        All additional keyword arguments are passed to ``ipyleaflet.TileLayer``.

    Returns
    -------
    ipyleaflet.TileLayer
        The tile layer that can be added to an ``ipyleaflet.Map``.
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
            stacklevel=2,
        )
    elif "bands" in kwargs:
        indexes = kwargs.pop("bands")
        warnings.warn(
            "The `bands` keyword argument is deprecated. Please use `indexes` instead.",
            stacklevel=2,
        )
    if "cmap" in kwargs:
        colormap = kwargs.pop("cmap")
        warnings.warn(
            "The `cmap` keyword argument is deprecated. Please use `colormap` instead.",
            stacklevel=2,
        )

    class BoundTileLayer(TileLayer, LocalTileServerLayerMixin):
        """
        TileLayer subclass that supports a bounds trait.
        """

        # https://github.com/jupyter-widgets/ipyleaflet/issues/888
        # https://github.com/ipython/traitlets/issues/626#issuecomment-699957829
        bounds = Union((Tuple(),), default_value=None, allow_none=True).tag(sync=True, o=True)

    source, _created = get_or_create_tile_client(
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
    # Always store reference to prevent the client from being garbage collected (#239)
    tile_layer.tile_server = source
    return tile_layer


def get_folium_tile_layer(
    source: pathlib.Path | str | TileClient | rasterio.io.DatasetReaderBase,
    port: int | str = "default",
    debug: bool = False,
    indexes: list[int] | None = None,
    colormap: str | None = None,
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
    nodata: int | float | None = None,
    attr: str | None = None,
    **kwargs,
):
    """
    Generate a folium TileLayer for the given TileClient.

    Parameters
    ----------
    source : pathlib.Path or str or TileClient or rasterio.io.DatasetReaderBase
        The source of the tile layer. This can be a path on disk or an already
        open ``TileClient``.
    port : int or str, optional
        The port on your host machine to use for the tile server (if creating
        a tileserver). This is ignored if a ``TileClient`` is given. This
        defaults to getting an available port.
    debug : bool, optional
        Run the tile server in debug mode (if creating a tileserver). This is
        ignored if a ``TileClient`` is given.
    indexes : list of int, optional
        The band of the source raster to use (default if ``None`` is to show
        RGB if available). Band indexing starts at 1. This can also be a list
        of integers to set which 3 bands to use for RGB.
    colormap : str, optional
        The name of the matplotlib colormap to use when plotting a single band.
        Default is greyscale.
    vmin : float or list of float, optional
        The minimum value to use when colormapping a single band.
    vmax : float or list of float, optional
        The maximum value to use when colormapping a single band.
    nodata : int or float, optional
        The value from the band to use to interpret as not valid data.
    attr : str, optional
        Folium requires the custom tile source have an attribution. This
        defaults to a message about it being a local file.
    **kwargs
        All additional keyword arguments are passed to ``folium.TileLayer``.

    Returns
    -------
    folium.TileLayer
        The tile layer that can be added to a ``folium.Map``.
    """
    # Safely import folium
    try:
        from folium import TileLayer
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `folium`: {e}") from e

    if "band" in kwargs:
        indexes = kwargs.pop("band")
        warnings.warn(
            "The `band` keyword argument is deprecated. Please use `indexes` instead.",
            stacklevel=2,
        )
    elif "bands" in kwargs:
        indexes = kwargs.pop("bands")
        warnings.warn(
            "The `bands` keyword argument is deprecated. Please use `indexes` instead.",
            stacklevel=2,
        )
    if "cmap" in kwargs:
        colormap = kwargs.pop("cmap")
        warnings.warn(
            "The `cmap` keyword argument is deprecated. Please use `colormap` instead.",
            stacklevel=2,
        )

    class FoliumTileLayer(TileLayer, LocalTileServerLayerMixin):
        """
        TileLayer subclass that stores a reference to the tile server.
        """

    source, _created = get_or_create_tile_client(
        source,
        port=port,
        debug=debug,
    )
    # On Colab, folium renders as static HTML so the browser needs a
    # publicly reachable proxy URL instead of localhost (#242).
    if _is_colab():
        proxy_url = _get_colab_proxy_url(source.server_port)
        if proxy_url:
            source.client_host = proxy_url
            source.client_port = None
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
    # Always store reference to prevent the client from being garbage collected (#239)
    tile_layer.tile_server = source
    return tile_layer
