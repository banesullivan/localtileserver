# flake8: noqa: W503
from collections.abc import Iterable
from functools import wraps
import json
import logging
import pathlib
from typing import List, Optional, Union
from urllib.parse import quote

from large_image.tilesource import FileTileSource
import requests

try:
    from rasterio.io import DatasetReaderBase
except ImportError:  # pragma: no cover
    DatasetReaderBase = None
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
from localtileserver.tileserver import get_building_docs, get_clean_filename, palette_valid_or_raise
from localtileserver.utilities import ImageBytes, add_query_parameters, save_file_from_request

BUILDING_DOCS = get_building_docs()
DEMO_REMOTE_TILE_SERVER = "https://tileserver.banesullivan.com/"
logger = logging.getLogger(__name__)


class BaseTileClient:
    """Base TileClient methods and configuration.

    This class does not perform any RESTful operations but will interface
    directly with large-image to produce results.

    Parameters
    ----------
    path : pathlib.Path, str
        The path on disk to use as the source raster for the tiles.

    """

    def __init__(
        self,
        filename: Union[pathlib.Path, str],
        default_projection: Optional[str] = "EPSG:3857",
    ):
        self._filename = get_clean_filename(filename)
        self._metadata = {}
        self._is_geospatial = None

        if default_projection != "EPSG:3857":
            self._default_projection = default_projection
        else:
            self._default_projection = ""

    @property
    def filename(self):
        return self._filename

    @property
    def default_projection(self):
        if self._default_projection == "":
            self._default_projection = "EPSG:3857" if self.is_geospatial else None
        return self._default_projection

    @default_projection.setter
    def default_projection(self, value):
        self._default_projection = value

    @property
    def rasterio(self):
        """Open dataset with rasterio."""
        if hasattr(self, "_rasterio_ds"):
            return self._rasterio_ds
        import rasterio

        self._rasterio_ds = rasterio.open(self.filename, "r")
        return self._rasterio_ds

    @property
    def server_host(self):
        raise NotImplementedError  # pragma: no cover

    @property
    def server_port(self):
        raise NotImplementedError  # pragma: no cover

    @property
    def server_base_url(self):
        raise NotImplementedError  # pragma: no cover

    def _produce_url(self, base: str):
        return add_query_parameters(base, {"filename": self._filename})

    def create_url(self, path: str, **kwargs):
        return self._produce_url(f"{self.server_base_url}/{path.lstrip('/')}")

    def _get_style_params(
        self,
        band: Union[int, List[int]] = None,
        palette: Union[str, List[str]] = None,
        vmin: Union[Union[float, int], List[Union[float, int]]] = None,
        vmax: Union[Union[float, int], List[Union[float, int]]] = None,
        nodata: Union[Union[float, int], List[Union[float, int]]] = None,
        scheme: Union[str, List[str]] = None,
        n_colors: int = 255,
        style: dict = None,
        cmap: Union[str, List[str]] = None,
    ):
        if style:
            return {"style": quote(json.dumps(style))}
        # First handle query parameters to check for errors
        params = {}
        if band is not None:
            params["band"] = band
        if palette is not None or cmap is not None:
            if palette is None:
                palette = cmap
            # make sure palette is valid
            palette_valid_or_raise(palette)
            params["palette"] = palette
        if vmin is not None:
            if isinstance(vmin, Iterable) and not isinstance(band, Iterable):
                raise ValueError("`band` must be explicitly set if `vmin` is an iterable.")
            params["min"] = vmin
        if vmax is not None:
            if isinstance(vmax, Iterable) and not isinstance(band, Iterable):
                raise ValueError("`band` must be explicitly set if `vmax` is an iterable.")
            params["max"] = vmax
        if nodata is not None:
            if isinstance(nodata, Iterable) and not isinstance(band, Iterable):
                raise ValueError("`band` must be explicitly set if `nodata` is an iterable.")
            params["nodata"] = nodata
        if scheme is not None:
            if (not isinstance(scheme, str) and isinstance(scheme, Iterable)) and not isinstance(
                band, Iterable
            ):
                raise ValueError("`band` must be explicitly set if `scheme` is an iterable.")
            params["scheme"] = scheme
        if n_colors:
            params["n_colors"] = n_colors
        return params

    def get_tile_url_params(
        self,
        projection: Optional[str] = "",
        band: Union[int, List[int]] = None,
        palette: Union[str, List[str]] = None,
        vmin: Union[Union[float, int], List[Union[float, int]]] = None,
        vmax: Union[Union[float, int], List[Union[float, int]]] = None,
        nodata: Union[Union[float, int], List[Union[float, int]]] = None,
        scheme: Union[str, List[str]] = None,
        n_colors: int = 255,
        grid: bool = False,
        style: dict = None,
        cmap: Union[str, List[str]] = None,
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
        grid : bool
            Show the outline of each tile. This is useful when debugging your
            tile viewer.
        style : dict, optional
            large-image JSON style. See
            https://girder.github.io/large_image/tilesource_options.html#style
            If given, this will override all other styling parameters.
        cmap : str
            Alias for palette if not specified.

        """
        params = self._get_style_params(
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            scheme=scheme,
            n_colors=n_colors,
            style=style,
            cmap=cmap,
        )
        if not projection:
            projection = self.default_projection
        params["projection"] = projection
        if grid:
            params["grid"] = True
        return params

    @wraps(get_tile_url_params)
    def get_tile_url(self, *args, client: bool = False, **kwargs):
        params = self.get_tile_url_params(*args, **kwargs)
        return add_query_parameters(
            self.create_url("api/tiles/{z}/{x}/{y}.png", client=client), params
        )

    def get_tile(self, z: int, x: int, y: int, *args, **kwargs):
        """Get single tile binary."""
        raise NotImplementedError  # pragma: no cover

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
        """Extract ROI in world coordinates."""
        raise NotImplementedError  # pragma: no cover

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

    def extract_roi_pixel(
        self,
        left: int,
        right: int,
        bottom: int,
        top: int,
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
        return_bytes: bool = False,
        return_path: bool = False,
    ):
        """Extract ROI in pixel coordinates."""
        raise NotImplementedError  # pragma: no cover

    def metadata(self, projection: Optional[str] = ""):
        raise NotImplementedError  # pragma: no cover

    def metadata_safe(self, projection: Optional[str] = ""):
        if self.is_geospatial:
            m = self.metadata(projection=projection)
        else:
            m = self.metadata(projection=None)
        return m

    def bounds(
        self, projection: str = "EPSG:4326", return_polygon: bool = False, return_wkt: bool = False
    ):
        """Get bounds in form of (ymin, ymax, xmin, xmax).

        Parameters
        ----------
        projection : str
            The EPSG projection of the returned coordinates. Can also be a
            Proj4 projection.

        return_polygon : bool, optional
            If true, return a shapely.Polygon object of the bounding polygon
            of the raster.

        return_wkt : bool, optional
            If true, return Well Known Text (WKT) string of the bounding
            polygon of the raster.

        """
        raise NotImplementedError  # pragma: no cover

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
        band: Union[int, List[int]] = None,
        palette: Union[str, List[str]] = None,
        vmin: Union[Union[float, int], List[Union[float, int]]] = None,
        vmax: Union[Union[float, int], List[Union[float, int]]] = None,
        nodata: Union[Union[float, int], List[Union[float, int]]] = None,
        scheme: Union[str, List[str]] = None,
        n_colors: int = 255,
        output_path: pathlib.Path = None,
        style: dict = None,
        cmap: Union[str, List[str]] = None,
        encoding: str = "PNG",
    ):
        raise NotImplementedError  # pragma: no cover

    def pixel(self, y: float, x: float, units: str = "pixels", projection: Optional[str] = None):
        """Get pixel values for each band at the given coordinates (y <lat>, x <lon>).

        Parameters
        ----------
        y : float
            The Y coordinate (from top of image if `pixels` units or latitude if using EPSG)
        x : float
            The X coordinate (from left of image if `pixels` units or longitude if using EPSG)
        units : str
            The units of the coordinates (`pixels` or `EPSG:4326`).
        projection : str, optional
            The projection in which to open the image.

        """
        raise NotImplementedError  # pragma: no cover

    def histogram(self, bins: int = 256, density: bool = False):
        """Get a histoogram for each band."""
        raise NotImplementedError  # pragma: no cover

    @property
    def default_zoom(self):
        m = self.metadata_safe()
        try:
            return m["levels"] - m["sourceLevels"]
        except KeyError:
            return 0

    @property
    def max_zoom(self):
        m = self.metadata_safe()
        return m.get("levels")

    @property
    def is_geospatial(self):
        if self._is_geospatial is None:
            self._is_geospatial = self.metadata(projection=None).get("geospatial", False)
        return self._is_geospatial

    if ipyleaflet:

        def _ipython_display_(self):
            from IPython.display import display
            from ipyleaflet import Map, WKTLayer, projections

            from localtileserver.widgets import get_leaflet_tile_layer

            t = get_leaflet_tile_layer(self)
            if self.default_projection is None:
                m = Map(
                    basemap=t,
                    min_zoom=0,
                    max_zoom=self.max_zoom,
                    zoom=0,
                    crs=projections.Simple,
                )
            else:
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


class RestfulTileClient(BaseTileClient):
    """Connect to a localtileserver instance.

    This is a base class for performing all operations over the RESTful API.

    """

    def get_tile(self, z: int, x: int, y: int, *args, output_path=None, **kwargs):
        url = self.get_tile_url(*args, **kwargs)
        r = requests.get(url.format(z=z, x=x, y=y))
        r.raise_for_status()
        if output_path:
            return save_file_from_request(r, output_path)
        return ImageBytes(r.content, mimetype=r.headers["Content-Type"])

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
        path = f"api/world/region.tif?units={units}&encoding={encoding}&left={left}&right={right}&bottom={bottom}&top={top}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        if return_bytes:
            return ImageBytes(r.content, mimetype=r.headers["Content-Type"])
        output_path = save_file_from_request(r, output_path)
        if return_path:
            return output_path
        return TileClient(output_path)

    def extract_roi_pixel(
        self,
        left: int,
        right: int,
        bottom: int,
        top: int,
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
        return_bytes: bool = False,
        return_path: bool = False,
    ):
        path = f"/api/pixel/region.tif?encoding={encoding}&left={left}&right={right}&bottom={bottom}&top={top}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        if return_bytes:
            return ImageBytes(r.content, mimetype=r.headers["Content-Type"])
        output_path = save_file_from_request(r, output_path)
        if return_path:
            return output_path
        return TileClient(
            output_path, default_projection="EPSG:3857" if encoding == "TILED" else None
        )

    def metadata(self, projection: Optional[str] = ""):
        if projection not in self._metadata:
            if projection == "":
                projection = self.default_projection
            r = requests.get(self.create_url(f"/api/metadata?projection={projection}"))
            r.raise_for_status()
            self._metadata[projection] = r.json()
        return self._metadata[projection]

    def bounds(
        self, projection: str = "EPSG:4326", return_polygon: bool = False, return_wkt: bool = False
    ):
        r = requests.get(
            self.create_url(f"/api/bounds?units={projection}&projection={self.default_projection}")
        )
        r.raise_for_status()
        bounds = r.json()
        extent = (bounds["ymin"], bounds["ymax"], bounds["xmin"], bounds["xmax"])
        if not return_polygon and not return_wkt:
            return extent
        # Safely import shapely
        try:
            from shapely.geometry import Polygon
        except ImportError as e:  # pragma: no cover
            raise ImportError(f"Please install `shapely`: {e}")
        coords = (
            (bounds["xmin"], bounds["ymax"]),
            (bounds["xmin"], bounds["ymax"]),
            (bounds["xmax"], bounds["ymax"]),
            (bounds["xmax"], bounds["ymin"]),
            (bounds["xmin"], bounds["ymin"]),
            (bounds["xmin"], bounds["ymax"]),  # Close the loop
        )
        poly = Polygon(coords)
        if return_wkt:
            return poly.wkt
        return poly

    def thumbnail(
        self,
        band: Union[int, List[int]] = None,
        palette: Union[str, List[str]] = None,
        vmin: Union[Union[float, int], List[Union[float, int]]] = None,
        vmax: Union[Union[float, int], List[Union[float, int]]] = None,
        nodata: Union[Union[float, int], List[Union[float, int]]] = None,
        scheme: Union[str, List[str]] = None,
        n_colors: int = 255,
        output_path: pathlib.Path = None,
        style: dict = None,
        cmap: Union[str, List[str]] = None,
        encoding: str = "PNG",
    ):
        if encoding.lower() not in ["png", "jpeg", "jpg", "tiff", "tif"]:
            raise ValueError(f"Encoding ({encoding}) not supported.")
        params = self._get_style_params(
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            scheme=scheme,
            n_colors=n_colors,
            style=style,
            cmap=cmap,
        )
        url = add_query_parameters(self.create_url(f"api/thumbnail.{encoding.lower()}"), params)
        r = requests.get(url)
        r.raise_for_status()
        if output_path:
            return save_file_from_request(r, output_path)
        return ImageBytes(r.content, mimetype=r.headers["Content-Type"])

    def pixel(self, y: float, x: float, units: str = "pixels", projection: Optional[str] = None):
        params = {}
        params["x"] = x
        params["y"] = y
        params["units"] = units
        if projection:
            params["projection"] = projection
        url = add_query_parameters(self.create_url("api/pixel"), params)
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def histogram(self, bins: int = 256, density: bool = False):
        params = {}
        params["density"] = density
        params["bins"] = bins
        url = add_query_parameters(self.create_url("api/histogram"), params)
        r = requests.get(url)
        r.raise_for_status()
        return r.json()


class RemoteTileClient(RestfulTileClient):
    """Connect to a remote localtileserver instance at a given host URL.

    Parameters
    ----------
    path : pathlib.Path, str
        The path on disk to use as the source raster for the tiles.
    host : str
        The base URL of your remote localtileserver instance.

    """

    def __init__(
        self,
        filename: Union[pathlib.Path, str],
        default_projection: Optional[str] = "EPSG:3857",
        host: str = None,
    ):
        super().__init__(filename=filename, default_projection=default_projection)
        if host is None:
            host = DEMO_REMOTE_TILE_SERVER
            logger.error(
                "WARNING: You are using a demo instance of localtileserver that has incredibly limited resources: it is unreliable and prone to crash. Please launch your own remote instance of localtileserver."
            )
        self._host = host

    @property
    def server_host(self):
        return self._host

    @server_host.setter
    def server_host(self, host):
        self._host = host

    @property
    def server_base_url(self):
        return self.server_host


class TileClient(RestfulTileClient):
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
        filename: Union[pathlib.Path, str, DatasetReaderBase, FileTileSource],
        default_projection: Optional[str] = "EPSG:3857",
        port: Union[int, str] = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int = None,
        client_host: str = None,
        client_prefix: str = None,
        cors_all: bool = False,
    ):
        if (
            DatasetReaderBase
            and isinstance(filename, DatasetReaderBase)
            and hasattr(filename, "name")
        ):
            filename = filename.name
        elif isinstance(filename, FileTileSource):
            filename = filename._getLargeImagePath()
        super().__init__(filename=filename, default_projection=default_projection)
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
            logging.getLogger("gdal").setLevel(logging.ERROR)
            logging.getLogger("large_image").setLevel(logging.ERROR)
        else:
            logging.getLogger("gdal").setLevel(logging.DEBUG)
            logging.getLogger("large_image").setLevel(logging.DEBUG)
            logging.getLogger("large_image_source_gdal").setLevel(logging.DEBUG)

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

    def create_url(self, path: str, client: bool = False):
        if client and (
            self.client_port is not None
            or self.client_host is not None
            or self.client_prefix is not None
        ):
            return self._produce_url(f"{self.client_base_url}/{path.lstrip('/')}")
        return self._produce_url(f"{self.server_base_url}/{path.lstrip('/')}")

    @wraps(BaseTileClient.get_tile_url_params)
    def get_tile_url(self, *args, client: bool = False, **kwargs):
        params = self.get_tile_url_params(*args, **kwargs)
        return add_query_parameters(
            self.create_url("api/tiles/{z}/{x}/{y}.png", client=client), params
        )


def get_or_create_tile_client(
    source: Union[pathlib.Path, str, TileClient, DatasetReaderBase, FileTileSource],
    port: Union[int, str] = "default",
    debug: bool = False,
    default_projection: Optional[str] = "EPSG:3857",
):
    """A helper to safely get a TileClient from a path on disk.

    Note
    ----
    TODO: There should eventually be a check to see if a TileClient instance exists
    for the given filename. For now, it is not really a big deal because the
    default is for all TileClient's to share a single server.

    """
    if isinstance(source, RemoteTileClient):
        return source, False
    _internally_created = False
    # Launch tile server if file path is given
    if not isinstance(source, TileClient):
        source = TileClient(source, port=port, debug=debug, default_projection=default_projection)
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
