import logging
import os
import pathlib
from typing import List, Union

from localtileserver.server import TileClient, get_or_create_tile_client

logger = logging.getLogger(__name__)
DEFAULT_ATTRIBUTION = "Raster file served by <a href='https://github.com/banesullivan/localtileserver' target='_blank'>localtileserver</a>."


def get_leaflet_tile_layer(
    source: Union[pathlib.Path, str, TileClient],
    port: Union[int, str] = "default",
    debug: bool = False,
    projection: str = "EPSG:3857",
    band: Union[int, List[int]] = None,
    palette: Union[str, List[str]] = None,
    vmin: Union[Union[float, int], List[Union[float, int]]] = None,
    vmax: Union[Union[float, int], List[Union[float, int]]] = None,
    nodata: Union[Union[float, int], List[Union[float, int]]] = None,
    attribution: str = None,
    **kwargs,
):
    """Generate an ipyleaflet TileLayer for the given TileClient.

    Parameters
    ----------
    source : Union[pathlib.Path, str, TileClient]
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
    except ImportError as e:
        raise ImportError(f"Please install `ipyleaflet`: {e}")
    source, created = get_or_create_tile_client(source, port=port, debug=debug)
    url = source.get_tile_url(
        projection=projection,
        band=band,
        palette=palette,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
    )
    if attribution is None:
        attribution = DEFAULT_ATTRIBUTION
    tile_layer = TileLayer(url=url, attribution=attribution, **kwargs)
    if created:
        # HACK: Prevent the client from being garbage collected
        tile_layer.tile_server = source
    return tile_layer


def get_leaflet_roi_controls(
    tile_client: TileClient,
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
    except ImportError as e:
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
        split = os.path.basename(tile_client.filename).split(".")
        ext = split[-1]
        basename = ".".join(split[:1])
        output_path = pathlib.Path(output_directory).absolute()
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / f"roi_{basename}_{left}_{right}_{bottom}_{top}.{ext}"
        draw_control.output_path = output_path
        logger.error(f"output_path: {output_path}")
        tile_client.extract_roi(left, right, bottom, top, output_path=output_path)

    button = widgets.Button(description="Extract ROI")
    button.on_click(on_button_clicked)
    button_control = WidgetControl(widget=button, position=button_position)
    if debug:
        return draw_control, button_control, debug_view
    return draw_control, button_control


def get_folium_tile_layer(
    source: Union[pathlib.Path, str, TileClient],
    port: Union[int, str] = "default",
    debug: bool = False,
    projection: str = "EPSG:3857",
    band: Union[int, List[int]] = None,
    palette: Union[str, List[str]] = None,
    vmin: Union[Union[float, int], List[Union[float, int]]] = None,
    vmax: Union[Union[float, int], List[Union[float, int]]] = None,
    nodata: Union[Union[float, int], List[Union[float, int]]] = None,
    attr: str = None,
    **kwargs,
):
    """Generate a folium TileLayer for the given TileClient.

    Parameters
    ----------
    source : Union[pathlib.Path, str, TileClient]
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
    except ImportError as e:
        raise ImportError(f"Please install `folium`: {e}")
    source, created = get_or_create_tile_client(source, port=port, debug=debug)
    url = source.get_tile_url(
        projection=projection,
        band=band,
        palette=palette,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
    )
    if attr is None:
        attr = DEFAULT_ATTRIBUTION
    tile_layer = TileLayer(tiles=url, attr=attr, **kwargs)
    if created:
        # HACK: Prevent the client from being garbage collected
        tile_layer.tile_server = source
    return tile_layer
