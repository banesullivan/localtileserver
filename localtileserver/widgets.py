import logging
import os
import pathlib
from typing import List, Optional, Union

try:
    from rasterio.io import DatasetReaderBase
except ImportError:
    DatasetReaderBase = None

from localtileserver.client import TileClient, get_or_create_tile_client

logger = logging.getLogger(__name__)
DEFAULT_ATTRIBUTION = "Raster file served by <a href='https://github.com/banesullivan/localtileserver' target='_blank'>localtileserver</a>."


class LocalTileServerLayerMixin:
    """Mixin class for tile layers using localtileserver."""

    pass


def get_leaflet_tile_layer(
    source: Union[pathlib.Path, str, TileClient, DatasetReaderBase],
    port: Union[int, str] = "default",
    debug: bool = False,
    projection: Optional[str] = "",
    band: Union[int, List[int]] = None,
    palette: Union[str, List[str]] = None,
    vmin: Union[Union[float, int], List[Union[float, int]]] = None,
    vmax: Union[Union[float, int], List[Union[float, int]]] = None,
    nodata: Union[Union[float, int], List[Union[float, int]]] = None,
    scheme: Union[str, List[str]] = None,
    n_colors: int = 255,
    attribution: str = None,
    style: dict = None,
    cmap: Union[str, List[str]] = None,
    default_projection: Optional[str] = "EPSG:3857",
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
    projection : str
        The Proj projection to use for the tile layer. Default is `EPSG:3857`.
    band : int
        The band of the source raster to use (default in None to show RGB if
        available). Band indexing starts at 1. This can also be a list of
        integers to set which 3 bands to use for RGB.
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
    scheme : str
        This is either ``linear`` (the default) or ``discrete``. If a
        palette is specified, ``linear`` uses a piecewise linear
        interpolation, and ``discrete`` uses exact colors from the palette
        with the range of the data mapped into the specified number of
        colors (e.g., a palette with two colors will split exactly halfway
        between the min and max values).
    n_colors : int
        The number (positive integer) of colors to discretize the matplotlib
        color palettes when used.
    attribution : str
        Attribution for the source raster. This
        defaults to a message about it being a local file.
    style : dict, optional
        large-image JSON style. See
        https://girder.github.io/large_image/tilesource_options.html#style
        If given, this will override all other styling parameters.
    cmap : str
        Alias for palette if not specified.
    **kwargs
        All additional keyword arguments are passed to ``ipyleaflet.TileLayer``.

    Return
    ------
    ipyleaflet.TileLayer

    """
    # Safely import ipyleaflet
    try:
        from ipyleaflet import TileLayer, projections
        from traitlets import Tuple, Union
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `ipyleaflet`: {e}")

    class BoundTileLayer(TileLayer, LocalTileServerLayerMixin):
        # https://github.com/jupyter-widgets/ipyleaflet/issues/888
        # https://github.com/ipython/traitlets/issues/626#issuecomment-699957829
        bounds = Union((Tuple(),), default_value=None, allow_none=True).tag(sync=True, o=True)

    source, created = get_or_create_tile_client(
        source, port=port, debug=debug, default_projection=default_projection
    )
    url = source.get_tile_url(
        projection=projection,
        band=kwargs.get("bands", band),
        palette=palette,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
        scheme=scheme,
        n_colors=n_colors,
        style=style,
        cmap=cmap,
        client=True,
    )
    if attribution is None:
        attribution = DEFAULT_ATTRIBUTION
    kwargs.setdefault("max_native_zoom", source.max_zoom)
    kwargs.setdefault("max_zoom", source.max_zoom)
    kwargs.setdefault("show_loading", True)
    if projection is None or (not projection and source.default_projection is None):
        kwargs.setdefault("crs", projections.Simple)
        bounds = None
    else:
        b = source.bounds()
        bounds = ((b[0], b[2]), (b[1], b[3]))
    tile_layer = BoundTileLayer(url=url, attribution=attribution, bounds=bounds, **kwargs)
    if created:
        # HACK: Prevent the client from being garbage collected
        tile_layer.tile_server = source
    return tile_layer


def get_leaflet_roi_controls(
    client: TileClient,
    button_position: str = "topright",
    output_directory: pathlib.Path = ".",
    debug: bool = False,
):
    """Generate an ipyleaflet DrawControl and WidgetControl to add to your map for ROI extraction.

    Parameters
    ----------
    button_position : str
        The button position of the WidgetControl.
    output_directory : pathlib.Path
        The directory to save the ROIs. Defaults to working directory.
    debug : bool
        Return a `widgets.Output` to debug the ROI extraction callback.

    Returns
    -------
    tuple(ipyleaflet.DrawControl, ipyleaflet.WidgetControl)

    """
    # Safely import ipyleaflet
    try:
        from ipyleaflet import DrawControl, WidgetControl
        import ipywidgets as widgets
        from shapely.geometry import Polygon
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `ipyleaflet` and `shapely`: {e}")
    draw_control = DrawControl()
    # Disable polyline and circle
    draw_control.polyline = {}
    draw_control.circlemarker = {}
    draw_control.polygon = {
        "shapeOptions": {
            "fillColor": "#6be5c3",
            "color": "#6be5c3",
            "fillOpacity": 0.75,
        },
    }
    draw_control.rectangle = {
        "shapeOptions": {
            "fillColor": "#fca45d",
            "color": "#fca45d",
            "fillOpacity": 0.75,
        }
    }

    # Set up the "Extract ROI" button
    debug_view = widgets.Output(layout={"border": "1px solid black"})

    @debug_view.capture(clear_output=False)
    def on_button_clicked(b):
        logger.error(f"\non_button_clicked {button_position}")
        # Inspect `draw_control.data` to get the ROI
        if not draw_control.data:
            # No ROI to extract
            logger.error("No polygons on map to use.")
            return
        p = None
        for poly in draw_control.data:
            t = Polygon([tuple(coord) for coord in poly["geometry"]["coordinates"][0]])
            if not p:
                p = t
            else:
                p = p.union(t)
        left, bottom, right, top = p.bounds
        # Get filename in working directory
        split = os.path.basename(client.filename).split(".")
        ext = split[-1]
        basename = ".".join(split[:1])
        output_path = pathlib.Path(output_directory).absolute()
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / f"roi_{basename}_{left}_{right}_{bottom}_{top}.{ext}"
        draw_control.output_path = output_path
        logger.error(f"output_path: {output_path}")
        client.extract_roi(left, right, bottom, top, output_path=output_path, return_path=True)

    button = widgets.Button(description="Extract ROI")
    button.on_click(on_button_clicked)
    button_control = WidgetControl(widget=button, position=button_position)
    if debug:
        return draw_control, button_control, debug_view
    return draw_control, button_control


def get_folium_tile_layer(
    source: Union[pathlib.Path, str, TileClient, DatasetReaderBase],
    port: Union[int, str] = "default",
    debug: bool = False,
    projection: Optional[str] = "",
    band: Union[int, List[int]] = None,
    palette: Union[str, List[str]] = None,
    vmin: Union[Union[float, int], List[Union[float, int]]] = None,
    vmax: Union[Union[float, int], List[Union[float, int]]] = None,
    nodata: Union[Union[float, int], List[Union[float, int]]] = None,
    scheme: Union[str, List[str]] = None,
    n_colors: int = 255,
    attr: str = None,
    style: dict = None,
    cmap: Union[str, List[str]] = None,
    default_projection: Optional[str] = "EPSG:3857",
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
    projection : str
        The Proj projection to use for the tile layer. Default is `EPSG:3857`.
    band : int
        The band of the source raster to use (default in None to show RGB if
        available). Band indexing starts at 1. This can also be a list of
        integers to set which 3 bands to use for RGB.
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
    scheme : str
        This is either ``linear`` (the default) or ``discrete``. If a
        palette is specified, ``linear`` uses a piecewise linear
        interpolation, and ``discrete`` uses exact colors from the palette
        with the range of the data mapped into the specified number of
        colors (e.g., a palette with two colors will split exactly halfway
        between the min and max values).
    n_colors : int
        The number (positive integer) of colors to discretize the matplotlib
        color palettes when used.
    attr : str
        Folium requires the custom tile source have an attribution. This
        defaults to a message about it being a local file.
    style : dict, optional
        large-image JSON style. See
        https://girder.github.io/large_image/tilesource_options.html#style
        If given, this will override all other styling parameters.
    cmap : str
        Alias for palette if not specified.
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

    class FoliumTileLayer(TileLayer, LocalTileServerLayerMixin):
        pass

    source, created = get_or_create_tile_client(
        source, port=port, debug=debug, default_projection=default_projection
    )
    url = source.get_tile_url(
        projection=projection,
        band=kwargs.get("bands", band),
        palette=palette,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
        scheme=scheme,
        n_colors=n_colors,
        style=style,
        cmap=cmap,
        client=True,
    )
    if attr is None:
        attr = DEFAULT_ATTRIBUTION
    if projection is None or (not projection and source.default_projection is None):
        kwargs.setdefault("crs", "Simple")
    tile_layer = FoliumTileLayer(tiles=url, attr=attr, **kwargs)
    if created:
        # HACK: Prevent the client from being garbage collected
        tile_layer.tile_server = source
    return tile_layer
