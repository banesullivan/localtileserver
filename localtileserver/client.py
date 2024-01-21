# flake8: noqa: W503
from collections.abc import Iterable
from functools import wraps
import json
import logging
import pathlib
import shutil
from typing import List, Optional, Union
from urllib.parse import quote

import rasterio
import requests

try:
    import ipyleaflet
except ImportError:  # pragma: no cover
    ipyleaflet = None
try:
    import shapely
except ImportError:  # pragma: no cover
    shapely = None

from server_thread import ServerManager, launch_server

from localtileserver.configure import get_default_client_params
from localtileserver.helpers import parse_shapely
from localtileserver.manager import AppManager
from localtileserver.tiler import (
    ImageBytes,
    format_to_encoding,
    get_building_docs,
    get_clean_filename,
    get_meta_data,
    get_point,
    get_preview,
    get_region_world,
    get_source_bounds,
    get_tile,
    get_tile_source,
    palette_valid_or_raise,
)
from localtileserver.utilities import add_query_parameters, save_file_from_request

BUILDING_DOCS = get_building_docs()
DEMO_REMOTE_TILE_SERVER = "https://tileserver.banesullivan.com/"
logger = logging.getLogger(__name__)


class LocalTileClient:
    """Base TileClient methods and configuration.

    This class interfaces directly with rasterio and rio-tiler.

    Parameters
    ----------
    path : pathlib.Path, str
        The path on disk to use as the source raster for the tiles.

    """

    def __init__(
        self,
        filename: Union[pathlib.Path, str],
    ):
        self._filename = get_clean_filename(filename)
        self._metadata = {}

        self._tile_source = get_tile_source(self.filename)

    @property
    def filename(self):
        return self._filename

    @property
    def tile_source(self):
        return self._tile_source

    @property
    def rasterio(self):
        return self._tile_source.dataset

    def _get_style_params(
        self,
        indexes: list[int] | None = None,
        colormap: str | None = None,
        nodata: int | float | None = None,
        vmin: float | None = None,
        vmax: float | None = None,
    ):
        # First handle query parameters to check for errors
        params = {}
        if indexes is not None:
            params["indexes"] = indexes
        if colormap is not None:
            # make sure palette is valid
            palette_valid_or_raise(colormap)
            params["colormap"] = colormap
        if vmin is not None:
            if isinstance(vmin, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `vmin` is an iterable.")
            params["min"] = vmin
        if vmax is not None:
            if isinstance(vmax, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `vmax` is an iterable.")
            params["max"] = vmax
        if nodata is not None:
            if isinstance(nodata, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `nodata` is an iterable.")
            params["nodata"] = nodata
        return params

    def get_tile_url_params(
        self,
        indexes: list[int] | None = None,
        colormap: str | None = None,
        nodata: int | float | None = None,
        vmin: float | None = None,
        vmax: float | None = None,
    ):
        """Get slippy maps tile URL (e.g., `/zoom/x/y.png`).

        Parameters
        ----------
        projection : str
            The Proj projection to use for the tile layer. Default is `EPSG:3857`.
        band : int
            The band of the source raster to use (default in None to show RGB if
            available). Band indexing starts at 1. This can also be a list of
            integers to set which 3 bands to use for RGB.
        palette : str
            The name of the color palette from `palettable` or colormap from
            matplotlib to use when plotting a single band. Default is greyscale.
            If viewing a single band, a list of hex colors can be passed for a
            user-defined color palette.
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
        cmap : str
            Alias for palette if not specified.

        """
        params = self._get_style_params(
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
        )
        return params

    def get_tile(
        self,
        z: int,
        x: int,
        y: int,
        indexes: list[int] | None = None,
        colormap: str | None = None,
        nodata: int | float | None = None,
        vmin: float | None = None,
        vmax: float | None = None,
        output_path: pathlib.Path = None,
        encoding: str = "PNG",
        band: Union[int, List[int]] = None,
    ):
        if indexes is None:
            # TODO: properly deprecate
            indexes = band
        if encoding.lower() not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Encoding ({encoding}) not supported.")
        encoding = format_to_encoding(encoding)

        tile_source = get_tile_source(self.filename)
        # TODO: handle format and mimetype
        tile_binary = get_tile(
            tile_source,
            z,
            x,
            y,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
        )
        if output_path:
            with open(output_path, "wb") as f:
                f.write(tile_binary)
        return tile_binary

    def extract_roi(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        units: str = "EPSG:4326",
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
        return_bytes: bool = False,
        return_path: bool = False,
    ):
        path, mimetype = get_region_world(
            self.tile_source,
            left,
            right,
            bottom,
            top,
            units,
            encoding,
        )
        if output_path is not None:
            shutil.move(path, output_path)
        else:
            output_path = path
        if return_bytes:
            with open(output_path, "rb") as f:
                return ImageBytes(f.read(), mimetype=mimetype)
        if return_path:
            return output_path
        return TileClient(output_path)

    def extract_roi_shape(
        self,
        shape,
        units: str = "EPSG:4326",
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
        return_bytes: bool = False,
        return_path: bool = False,
    ):
        """Extract ROI in world coordinates using a Shapely Polygon.

        Parameters
        ----------
        shape
            Anything shape-like (GeoJSON dict, WKT string, Shapely.Polygon) or
            anything with a ``bounds`` property that returns the
            bounding coordinates of the shape as: ``left``, ``bottom``, ``right``,
            ``top``.

        """
        if not hasattr(shape, "bounds"):
            shape = parse_shapely(shape)
        left, bottom, right, top = shape.bounds
        return self.extract_roi(
            left,
            right,
            bottom,
            top,
            units=units,
            encoding=encoding,
            output_path=output_path,
            return_bytes=return_bytes,
            return_path=return_path,
        )

    def metadata(self, projection: Optional[str] = "EPSG:3857"):
        if projection not in self._metadata:
            tile_source = get_tile_source(self.filename)
            self._metadata[projection] = get_meta_data(tile_source)
        return self._metadata[projection]

    def metadata_safe(self, projection: Optional[str] = ""):
        return self.metadata(projection=projection)

    def bounds(
        self, projection: str = "EPSG:4326", return_polygon: bool = False, return_wkt: bool = False
    ):
        bounds = get_source_bounds(self.tile_source, projection=projection)
        extent = (bounds["bottom"], bounds["top"], bounds["left"], bounds["right"])
        if not return_polygon and not return_wkt:
            return extent
        # Safely import shapely
        try:
            from shapely.geometry import Polygon
        except ImportError as e:  # pragma: no cover
            raise ImportError(f"Please install `shapely`: {e}")
        coords = (
            (bounds["left"], bounds["top"]),
            (bounds["left"], bounds["top"]),
            (bounds["right"], bounds["top"]),
            (bounds["right"], bounds["bottom"]),
            (bounds["left"], bounds["bottom"]),
            (bounds["left"], bounds["top"]),  # Close the loop
        )
        poly = Polygon(coords)
        if return_wkt:
            return poly.wkt
        return poly

    def center(
        self, projection: str = "EPSG:4326", return_point: bool = False, return_wkt: bool = False
    ):
        """Get center in the form of (y <lat>, x <lon>).

        Parameters
        ----------
        projection : str
            The srs or projection as a Proj4 string of the returned coordinates

        return_point : bool, optional
            If true, returns a shapely.Point object.

        return_wkt : bool, optional
            If true, returns a Well Known Text (WKT) string of center
            coordinates.

        """
        bounds = self.bounds(projection=projection)
        point = (
            (bounds[1] - bounds[0]) / 2 + bounds[0],
            (bounds[3] - bounds[2]) / 2 + bounds[2],
        )
        if return_point or return_wkt:
            # Safely import shapely
            try:
                from shapely.geometry import Point
            except ImportError as e:  # pragma: no cover
                raise ImportError(f"Please install `shapely`: {e}")

            point = Point(point)
            if return_wkt:
                return point.wkt

        return point

    def thumbnail(
        self,
        cmap: Union[str, List[str]] = None,
        indexes: Union[int, List[int]] = None,
        vmin: Union[Union[float, int], List[Union[float, int]]] = None,
        vmax: Union[Union[float, int], List[Union[float, int]]] = None,
        nodata: Union[Union[float, int], List[Union[float, int]]] = None,
        scheme: Union[str, List[str]] = None,
        n_colors: int = 255,
        output_path: pathlib.Path = None,
        encoding: str = "PNG",
        band: Union[int, List[int]] = None,
        max_size: int = 512,
    ):
        if indexes is None:
            # TODO: properly deprecate
            indexes = band
        if encoding.lower() not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Encoding ({encoding}) not supported.")
        encoding = format_to_encoding(encoding)

        tile_source = get_tile_source(self.filename)
        thumb_data = get_preview(
            tile_source,
            max_size=max_size,
            colormap=cmap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
        )

        if output_path:
            with open(output_path, "wb") as f:
                f.write(thumb_data)
        return thumb_data

    def point(self, lon: float, lat: float, **kwargs):
        tile_source = get_tile_source(self.filename)
        return get_point(tile_source, lon, lat, **kwargs)

    @property
    def default_zoom(self):
        return 9  # TODO: implement this

    @property
    def max_zoom(self):
        m = self.metadata_safe()
        return m.get("levels")

    if ipyleaflet:

        def _ipython_display_(self):
            from IPython.display import display
            from ipyleaflet import Map, WKTLayer, projections

            from localtileserver.widgets import get_leaflet_tile_layer

            t = get_leaflet_tile_layer(self)
            m = Map(center=self.center(), zoom=self.default_zoom)
            m.add_layer(t)
            if shapely:
                wlayer = WKTLayer(
                    wkt_string=self.bounds(return_wkt=True),
                    style={"dashArray": 9, "fillOpacity": 0, "weight": 1},
                )
                m.add_layer(wlayer)
            return display(m)

    def _repr_png_(self):
        with open(self.thumbnail(encoding="PNG"), "rb") as f:
            return f.read()


class _TileServerManager:
    """Serve tiles from a local raster file in a background thread.

    Parameters
    ----------
    path : pathlib.Path, str, rasterio.io.DatasetReaderBase
        The path on disk to use as the source raster for the tiles.
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.
    client_port : int
        The port on your client browser to use for fetching tiles. This is
        useful when running in Docker and performing port forwarding.
    client_host : str
        The host on which your client browser can access the server.

    """

    def __init__(
        self,
        filename: Union[pathlib.Path, str, rasterio.io.DatasetReaderBase],
        port: Union[int, str] = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int = None,
        client_host: str = None,
        client_prefix: str = None,
        cors_all: bool = False,
    ):
        if isinstance(filename, rasterio.io.DatasetReaderBase) and hasattr(filename, "name"):
            filename = filename.name
        super().__init__(filename=filename)
        app = AppManager.get_or_create_app(cors_all=cors_all)
        self._key = launch_server(app, port=port, debug=debug, host=host)
        # Store actual port just in case
        self._port = ServerManager.get_server(self._key).srv.port
        client_host, client_port, client_prefix = get_default_client_params(
            client_host, client_port, client_prefix
        )
        self.client_host = client_host
        self.client_port = client_port
        self.client_prefix = client_prefix
        if BUILDING_DOCS and not client_host:
            self._client_host = DEMO_REMOTE_TILE_SERVER

        if not debug:
            logging.getLogger("rasterio").setLevel(logging.ERROR)
        else:
            logging.getLogger("rasterio").setLevel(logging.DEBUG)

        try:
            import google.colab  # noqa

            self.enable_colab()
        except ImportError:
            pass

    def shutdown(self, force: bool = False):
        if hasattr(self, "_key"):
            ServerManager.shutdown_server(self._key, force=force)

    def __del__(self):
        self.shutdown()

    @property
    def server(self):
        return ServerManager.get_server(self._key)

    @property
    def server_port(self):
        return self.server.port

    @property
    def server_host(self):
        return self.server.host

    @property
    def server_base_url(self):
        return f"http://{self.server_host}:{self.server_port}"

    @property
    def client_port(self):
        return self._client_port

    @client_port.setter
    def client_port(self, value):
        if value is True:
            value = self.server_port
        self._client_port = value

    @property
    def client_host(self):
        return self._client_host

    @client_host.setter
    def client_host(self, value):
        self._client_host = value

    @property
    def client_prefix(self):
        if self._client_prefix:
            return self._client_prefix.replace("{port}", str(self.server_port))

    @client_prefix.setter
    def client_prefix(self, value):
        self._client_prefix = value

    def enable_colab(self):
        """Configure this client for use on Google Colab."""
        self.client_host = "localhost"
        self.client_port = True

    @property
    def client_base_url(self):
        scheme = (
            "http://"
            if self.client_host is not None and not self.client_host.startswith("http")
            else ""
        )
        if self.client_port is not None and self.client_host is not None:
            base = f"{scheme}{self.client_host}:{self.client_port}"
        elif self.client_port is None and self.client_host is not None:
            base = f"{scheme}{self.client_host}"
        elif self.client_port is not None and self.client_host is None:
            base = f"http://{self.server_host}:{self.client_port}"
        else:
            base = "/"  # Use relative path
        if self.client_prefix is not None:
            base = f"{base}{self.client_prefix}"
        if base.startswith("/"):
            base = f"/{base.lstrip('/')}"
        return base

    def _produce_url(self, base: str):
        return add_query_parameters(base, {"filename": self._filename})

    def create_url(self, path: str, client: bool = False):
        if client and (
            self.client_port is not None
            or self.client_host is not None
            or self.client_prefix is not None
        ):
            return self._produce_url(f"{self.client_base_url}/{path.lstrip('/')}")
        return self._produce_url(f"{self.server_base_url}/{path.lstrip('/')}")

    @wraps(LocalTileClient.get_tile_url_params)
    def get_tile_url(self, *args, client: bool = False, **kwargs):
        params = self.get_tile_url_params(*args, **kwargs)
        url = add_query_parameters(
            self.create_url("api/tiles/{z}/{x}/{y}.png", client=client), params
        )
        print(url)
        return url


class TileClient(_TileServerManager, LocalTileClient):
    pass


def get_or_create_tile_client(
    source: Union[
        pathlib.Path,
        str,
        TileClient,
        rasterio.io.DatasetReaderBase,
    ],
    port: Union[int, str] = "default",
    debug: bool = False,
):
    """A helper to safely get a TileClient from a path on disk.

    Note
    ----
    TODO: There should eventually be a check to see if a TileClient instance exists
    for the given filename. For now, it is not really a big deal because the
    default is for all TileClient's to share a single server.

    """
    _internally_created = False
    # Launch tile server if file path is given
    if not isinstance(source, TileClient):
        source = TileClient(source, port=port, debug=debug)
        _internally_created = True

    # Check that the tile source is valid and no server errors
    try:
        r = requests.get(source.create_url("api/metadata"))
        r.raise_for_status()
    except requests.HTTPError as e:
        # Make sure to destroy the server and its thread if internally created.
        if _internally_created:
            source.shutdown()
            del source
        raise e
    return source, _internally_created
