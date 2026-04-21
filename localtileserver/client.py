"""
Tile client for serving and interacting with geospatial rasters.
"""

from collections.abc import Iterable
import json
import logging
import os
import pathlib

from matplotlib.colors import Colormap, LinearSegmentedColormap, ListedColormap
import rasterio
import requests
from rio_tiler.io import Reader

try:
    import ipyleaflet
    from ipyleaflet import Map, WKTLayer
    from IPython.display import display as _ipython_display_fn
except ImportError:  # pragma: no cover
    ipyleaflet = None
try:
    import shapely
except ImportError:  # pragma: no cover
    shapely = None

from server_thread import ServerManager, launch_server

from localtileserver.configure import get_default_client_params
from localtileserver.manager import AppManager
from localtileserver.tiler import (
    format_to_encoding,
    get_building_docs,
    get_feature,
    get_meta_data,
    get_part,
    get_point,
    get_preview,
    get_reader,
    get_source_bounds,
    get_tile,
    palette_valid_or_raise,
    register_colormap,
)
from localtileserver.tiler.handler import get_statistics
from localtileserver.tiler.stac import (
    get_stac_info,
    get_stac_preview,
    get_stac_reader,
    get_stac_statistics,
    get_stac_tile,
)
from localtileserver.utilities import add_query_parameters

BUILDING_DOCS = get_building_docs()
DEMO_REMOTE_TILE_SERVER = "https://tileserver.banesullivan.com/"
logger = logging.getLogger(__name__)


class TilerInterface:
    """
    Base TileClient methods and configuration.

    This class interfaces directly with rasterio and rio-tiler.

    Parameters
    ----------
    source : pathlib.Path, str, Reader, DatasetReaderBase
        The source dataset to use for the tile client.
    """

    def __init__(
        self,
        source: pathlib.Path | str | rasterio.io.DatasetReaderBase,
    ):
        if isinstance(source, rasterio.io.DatasetReaderBase):  # and hasattr(source, "name"):
            self._reader = get_reader(source.name)
        elif isinstance(source, Reader):
            self._reader = source
        else:
            self._reader = get_reader(source)

    @property
    def reader(self):
        """
        Return the rio-tiler Reader for the source dataset.

        Returns
        -------
        Reader
            The rio-tiler ``Reader`` instance.
        """
        return self._reader

    @property
    def dataset(self):
        """
        Return the underlying rasterio dataset.

        Returns
        -------
        rasterio.io.DatasetReaderBase
            The opened rasterio dataset.
        """
        return self.reader.dataset

    @property
    def filename(self):
        """
        Return the file path or URI of the source dataset.

        Returns
        -------
        str
            The file path or URI string.
        """
        return self.dataset.name

    @property
    def info(self):
        """
        Return dataset info from the rio-tiler reader.

        Returns
        -------
        rio_tiler.models.Info
            Dataset information including CRS, bounds, and band details.
        """
        return self.reader.info()

    @property
    def metadata(self):
        """
        Return metadata for the source dataset.

        Returns
        -------
        dict
            A dictionary of dataset metadata including band descriptions,
            data types, and statistics.
        """
        return get_meta_data(self.reader)

    @property
    def band_names(self):
        """
        Return the names of each band in the dataset.

        Returns
        -------
        list of str
            Band name strings extracted from the dataset metadata.
        """
        return [desc[0] for desc in self.metadata["band_descriptions"]]

    @property
    def min_zoom(self):
        """
        Return the minimum zoom level for the dataset.

        Returns
        -------
        int
            The minimum zoom level.
        """
        if hasattr(self.info, "minzoom"):
            return self.info.minzoom
        else:
            return self.reader.minzoom

    @property
    def max_zoom(self):
        """
        Return the maximum zoom level for the dataset.

        Returns
        -------
        int
            The maximum zoom level.
        """
        if hasattr(self.info, "maxzoom"):
            return self.info.maxzoom
        else:
            return self.reader.maxzoom

    @property
    def default_zoom(self):
        """
        Return the default zoom level for the dataset.

        This is set to :attr:`min_zoom`.

        Returns
        -------
        int
            The default zoom level.
        """
        return self.min_zoom

    def bounds(
        self, projection: str = "EPSG:4326", return_polygon: bool = False, return_wkt: bool = False
    ):
        """
        Get the bounds of the dataset.

        Parameters
        ----------
        projection : str, optional
            The spatial reference system as a Proj4 or EPSG string for the
            returned coordinates. Defaults to ``"EPSG:4326"``.
        return_polygon : bool, optional
            If ``True``, return a ``shapely.geometry.Polygon`` instead of a
            tuple. Requires ``shapely``.
        return_wkt : bool, optional
            If ``True``, return a Well Known Text (WKT) string of the
            bounding polygon. Requires ``shapely``.

        Returns
        -------
        tuple of float
            A tuple of ``(bottom, top, left, right)`` when neither
            ``return_polygon`` nor ``return_wkt`` is ``True``.
        shapely.geometry.Polygon
            When ``return_polygon`` is ``True``.
        str
            WKT string when ``return_wkt`` is ``True``.
        """
        bounds = get_source_bounds(self.reader, projection=projection)
        extent = (bounds["bottom"], bounds["top"], bounds["left"], bounds["right"])
        if not return_polygon and not return_wkt:
            return extent
        # Safely import shapely
        try:
            from shapely.geometry import Polygon
        except ImportError as e:  # pragma: no cover
            raise ImportError(f"Please install `shapely`: {e}") from e
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
        """
        Get center in the form of (y <lat>, x <lon>).

        Parameters
        ----------
        projection : str
            The srs or projection as a Proj4 string of the returned coordinates.

        return_point : bool, optional
            If true, returns a shapely.Point object.

        return_wkt : bool, optional
            If true, returns a Well Known Text (WKT) string of center
            coordinates.

        Returns
        -------
        tuple of float
            A tuple of ``(y, x)`` (latitude, longitude) when neither
            ``return_point`` nor ``return_wkt`` is ``True``.
        shapely.geometry.Point
            When ``return_point`` is ``True``.
        str
            WKT string when ``return_wkt`` is ``True``.
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
                raise ImportError(f"Please install `shapely`: {e}") from e

            point = Point(point)
            if return_wkt:
                return point.wkt

        return point

    def tile(
        self,
        z: int,
        x: int,
        y: int,
        indexes: list[int] | None = None,
        colormap: str | None = None,
        vmin: float | list[float] | None = None,
        vmax: float | list[float] | None = None,
        nodata: int | float | None = None,
        output_path: pathlib.Path | None = None,
        encoding: str = "PNG",
        expression: str | None = None,
        stretch: str | None = None,
    ):
        """
        Generate a tile from the source raster.

        Parameters
        ----------
        z : int
            The zoom level of the tile.
        x : int
            The x coordinate of the tile.
        y : int
            The y coordinate of the tile.
        indexes : list of int, optional
            The band(s) of the source raster to use (default if ``None`` is to
            show RGB if available). Band indexing starts at 1. This can also be
            a list of integers to set which 3 bands to use for RGB.
        colormap : str, optional
            The name of the matplotlib colormap to use when plotting a single
            band. Default is greyscale.
        vmin : float or list of float, optional
            The minimum value to use when colormapping a single band.
        vmax : float or list of float, optional
            The maximum value to use when colormapping a single band.
        nodata : int or float, optional
            The value from the band to use to interpret as not valid data.
        output_path : pathlib.Path, optional
            If provided, write the tile image to this file path.
        encoding : str, optional
            The image encoding format (e.g., ``"PNG"``, ``"JPEG"``).
            Defaults to ``"PNG"``.
        expression : str, optional
            Band math expression (e.g., ``"(b4-b1)/(b4+b1)"`` for NDVI).
            Mutually exclusive with ``indexes``.
        stretch : str, optional
            Image stretch mode. One of ``"none"``, ``"minmax"``,
            ``"linear"``, ``"equalize"``, ``"sqrt"``, or ``"log"``.
            When set, overrides ``vmin``/``vmax``.

        Returns
        -------
        bytes
            The tile image as binary data in the specified encoding.
        """
        if expression and indexes is not None:
            raise ValueError("Cannot use both 'expression' and 'indexes'.")
        encoding = format_to_encoding(encoding)
        tile_binary = get_tile(
            self.reader,
            z,
            x,
            y,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
            expression=expression,
            stretch=stretch,
        )
        if output_path:
            with open(output_path, "wb") as f:
                f.write(tile_binary)
        return tile_binary

    def statistics(
        self,
        indexes: list[int] | None = None,
        expression: str | None = None,
    ):
        """
        Get per-band statistics (min, max, mean, std, histogram).

        Parameters
        ----------
        indexes : list of int, optional
            Band indexes to compute statistics for.
        expression : str, optional
            Band math expression to compute statistics on.

        Returns
        -------
        dict
            Per-band statistics keyed by band name.
        """
        return get_statistics(self.reader, indexes=indexes, expression=expression)

    def thumbnail(
        self,
        indexes: list[int] | None = None,
        colormap: str | None = None,
        vmin: float | list[float] | None = None,
        vmax: float | list[float] | None = None,
        nodata: int | float | None = None,
        output_path: pathlib.Path | None = None,
        encoding: str = "PNG",
        max_size: int = 512,
        crs: str | None = None,
        expression: str | None = None,
        stretch: str | None = None,
    ):
        """
        Generate a thumbnail preview of the dataset.

        Parameters
        ----------
        indexes : list of int, optional
            The band(s) of the source raster to use (default if ``None`` is to
            show RGB if available). Band indexing starts at 1. This can also be
            a list of integers to set which 3 bands to use for RGB.
        colormap : str, optional
            The name of the matplotlib colormap to use when plotting a single
            band. Default is greyscale.
        vmin : float or list of float, optional
            The minimum value to use when colormapping a single band.
        vmax : float or list of float, optional
            The maximum value to use when colormapping a single band.
        nodata : int or float, optional
            The value from the band to use to interpret as not valid data.
        output_path : pathlib.Path, optional
            If provided, write the thumbnail image to this file path.
        encoding : str, optional
            The image encoding format (e.g., ``"PNG"``, ``"JPEG"``).
            Defaults to ``"PNG"``.
        max_size : int, optional
            Maximum size of the thumbnail in pixels. Defaults to 512.
        crs : str, optional
            Target CRS for the thumbnail projection (e.g., ``"EPSG:3857"``).
            When set, the preview is reprojected to this CRS.
        expression : str, optional
            Band math expression (e.g., ``"(b4-b1)/(b4+b1)"``).
            Mutually exclusive with ``indexes``.
        stretch : str, optional
            Image stretch mode. One of ``"none"``, ``"minmax"``,
            ``"linear"``, ``"equalize"``, ``"sqrt"``, or ``"log"``.
            When set, overrides ``vmin``/``vmax``.

        Returns
        -------
        bytes
            The thumbnail image as binary data in the specified encoding.
        """
        if expression and indexes is not None:
            raise ValueError("Cannot use both 'expression' and 'indexes'.")
        if encoding.lower() not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Encoding ({encoding}) not supported.")
        encoding = format_to_encoding(encoding)
        thumb_data = get_preview(
            self.reader,
            max_size=max_size,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
            crs=crs,
            expression=expression,
            stretch=stretch,
        )

        if output_path:
            with open(output_path, "wb") as f:
                f.write(thumb_data)
        return thumb_data

    def point(self, lon: float, lat: float, **kwargs):
        """
        Query pixel values at a geographic coordinate.

        Parameters
        ----------
        lon : float
            Longitude of the query point.
        lat : float
            Latitude of the query point.
        **kwargs
            Additional keyword arguments passed to the underlying
            ``get_point`` function.

        Returns
        -------
        dict
            Per-band pixel values at the queried location.
        """
        return get_point(self.reader, lon, lat, **kwargs)

    def part(
        self,
        bbox: tuple[float, float, float, float],
        indexes: list[int] | None = None,
        colormap: str | None = None,
        vmin: float | list[float] | None = None,
        vmax: float | list[float] | None = None,
        nodata: int | float | None = None,
        output_path: pathlib.Path | None = None,
        encoding: str = "PNG",
        max_size: int = 1024,
        dst_crs: str | None = None,
        bounds_crs: str | None = None,
        expression: str | None = None,
        stretch: str | None = None,
    ):
        """
        Extract a spatial subset by bounding box.

        Parameters
        ----------
        bbox : tuple of float
            Bounding box as ``(left, bottom, right, top)``.
        indexes : list of int, optional
            The band(s) of the source raster to use (default if ``None`` is to
            show RGB if available). Band indexing starts at 1.
        colormap : str, optional
            The name of the matplotlib colormap to use when plotting a single
            band. Default is greyscale.
        vmin : float or list of float, optional
            The minimum value to use when colormapping a single band.
        vmax : float or list of float, optional
            The maximum value to use when colormapping a single band.
        nodata : int or float, optional
            The value from the band to use to interpret as not valid data.
        output_path : pathlib.Path, optional
            If provided, write the image to this file path.
        encoding : str, optional
            The image encoding format (e.g., ``"PNG"``, ``"JPEG"``).
            Defaults to ``"PNG"``.
        max_size : int, optional
            Maximum dimension of the output image in pixels. Defaults to
            1024.
        dst_crs : str, optional
            Target CRS for the output image (e.g., ``"EPSG:3857"``).
        bounds_crs : str, optional
            CRS of the *bbox* coordinates. Defaults to the dataset's
            native CRS.
        expression : str, optional
            Band math expression (e.g., ``"(b4-b1)/(b4+b1)"``).
            Mutually exclusive with ``indexes``.
        stretch : str, optional
            Image stretch mode. One of ``"none"``, ``"minmax"``,
            ``"linear"``, ``"equalize"``, ``"sqrt"``, or ``"log"``.
            When set, overrides ``vmin``/``vmax``.

        Returns
        -------
        bytes
            The cropped image as binary data in the specified encoding.
        """
        if expression and indexes is not None:
            raise ValueError("Cannot use both 'expression' and 'indexes'.")
        encoding = format_to_encoding(encoding)
        result = get_part(
            self.reader,
            bbox,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
            max_size=max_size,
            dst_crs=dst_crs,
            bounds_crs=bounds_crs,
            expression=expression,
            stretch=stretch,
        )
        if output_path:
            with open(output_path, "wb") as f:
                f.write(result)
        return result

    def feature(
        self,
        geojson: dict,
        indexes: list[int] | None = None,
        colormap: str | None = None,
        vmin: float | list[float] | None = None,
        vmax: float | list[float] | None = None,
        nodata: int | float | None = None,
        output_path: pathlib.Path | None = None,
        encoding: str = "PNG",
        max_size: int = 1024,
        dst_crs: str | None = None,
        expression: str | None = None,
        stretch: str | None = None,
    ):
        """
        Extract data masked to a GeoJSON feature.

        Parameters
        ----------
        geojson : dict
            A GeoJSON Feature or Geometry dictionary. If a bare Geometry
            is provided, it is automatically wrapped in a Feature.
        indexes : list of int, optional
            The band(s) of the source raster to use (default if ``None`` is to
            show RGB if available). Band indexing starts at 1.
        colormap : str, optional
            The name of the matplotlib colormap to use when plotting a single
            band. Default is greyscale.
        vmin : float or list of float, optional
            The minimum value to use when colormapping a single band.
        vmax : float or list of float, optional
            The maximum value to use when colormapping a single band.
        nodata : int or float, optional
            The value from the band to use to interpret as not valid data.
        output_path : pathlib.Path, optional
            If provided, write the image to this file path.
        encoding : str, optional
            The image encoding format (e.g., ``"PNG"``, ``"JPEG"``).
            Defaults to ``"PNG"``.
        max_size : int, optional
            Maximum dimension of the output image in pixels. Defaults to
            1024.
        dst_crs : str, optional
            Target CRS for the output image (e.g., ``"EPSG:3857"``).
        expression : str, optional
            Band math expression (e.g., ``"(b4-b1)/(b4+b1)"``).
            Mutually exclusive with ``indexes``.
        stretch : str, optional
            Image stretch mode. One of ``"none"``, ``"minmax"``,
            ``"linear"``, ``"equalize"``, ``"sqrt"``, or ``"log"``.
            When set, overrides ``vmin``/``vmax``.

        Returns
        -------
        bytes
            The masked image as binary data in the specified encoding.
        """
        if expression and indexes is not None:
            raise ValueError("Cannot use both 'expression' and 'indexes'.")
        encoding = format_to_encoding(encoding)
        result = get_feature(
            self.reader,
            geojson,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
            max_size=max_size,
            dst_crs=dst_crs,
            expression=expression,
            stretch=stretch,
        )
        if output_path:
            with open(output_path, "wb") as f:
                f.write(result)
        return result

    def _repr_png_(self):
        """
        Return a PNG thumbnail for IPython/Jupyter rich display.
        """
        return self.thumbnail(encoding="png")


class TileServerMixin:
    """
    Serve tiles from a local raster file in a background thread.

    Parameters
    ----------
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.
    host : str
        The host address to bind the tile server to.
    client_port : int
        The port on your client browser to use for fetching tiles. This is
        useful when running in Docker and performing port forwarding.
    client_host : str
        The host on which your client browser can access the server.
    client_prefix : str
        The URL prefix used for proxied access to the tile server.
    cors_all : bool
        If ``True``, enable CORS for all origins on the tile server.
    """

    def __init__(
        self,
        port: int | str = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int | None = None,
        client_host: str | None = None,
        client_prefix: str | None = None,
        cors_all: bool = False,
    ):
        # Forward rasterio/GDAL env from the calling context so it is
        # available to the background tile-server thread (#182).
        # set_rasterio_env writes each option to os.environ so that GDAL
        # picks them up from any thread without per-request wrapping.
        rio_env = {}
        try:
            rio_env.update(rasterio.env.getenv())
        except Exception:
            pass
        # Also capture GDAL/AWS/CPL env vars from os.environ
        for key, val in os.environ.items():
            if key.startswith(("GDAL_", "AWS_", "CPL_")):
                rio_env.setdefault(key, val)
        if rio_env:
            AppManager.set_rasterio_env(rio_env)

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
        """
        Shut down the background tile server.

        Parameters
        ----------
        force : bool, optional
            If ``True``, forcefully terminate the server. Defaults to
            ``False``.
        """
        if hasattr(self, "_key"):
            ServerManager.shutdown_server(self._key, force=force)

    def __del__(self):
        self.shutdown()

    @property
    def server(self):
        """
        Return the background server instance.

        Returns
        -------
        server_thread.ServerThread
            The managed server thread.
        """
        return ServerManager.get_server(self._key)

    @property
    def server_port(self):
        """
        Return the port the tile server is listening on.

        Returns
        -------
        int
            The server port number.
        """
        return self.server.port

    @property
    def server_host(self):
        """
        Return the host the tile server is bound to.

        Returns
        -------
        str
            The server host address.
        """
        return self.server.host

    @property
    def server_base_url(self):
        """
        Return the base URL for the tile server.

        Returns
        -------
        str
            The full server base URL (e.g., ``"http://127.0.0.1:8080"``).
        """
        return f"http://{self.server_host}:{self.server_port}"

    @property
    def client_port(self):
        """
        Return the port used by the client browser to access tiles.

        Returns
        -------
        int or None
            The client-side port number, or ``None`` if not explicitly set.
        """
        return self._client_port

    @client_port.setter
    def client_port(self, value):
        """
        Set the client-side port, resolving ``True`` to the server port.

        Parameters
        ----------
        value : int, bool, or None
            Port number, ``True`` to use the server port, or ``None``.
        """
        if value is True:
            value = self.server_port
        self._client_port = value

    @property
    def client_host(self):
        """
        Return the host used by the client browser to access tiles.

        Returns
        -------
        str or None
            The client-side host address, or ``None`` if not explicitly set.
        """
        return self._client_host

    @client_host.setter
    def client_host(self, value):
        """
        Set the client-side host address.

        Parameters
        ----------
        value : str or None
            The host address string, or ``None``.
        """
        self._client_host = value

    @property
    def client_prefix(self):
        """
        Return the URL prefix used by the client for proxied access.

        Returns
        -------
        str or None
            The client URL prefix with ``{port}`` replaced by the actual
            server port, or ``None`` if not set.
        """
        if self._client_prefix:
            return self._client_prefix.replace("{port}", str(self.server_port))

    @client_prefix.setter
    def client_prefix(self, value):
        """
        Set the client URL prefix.

        Parameters
        ----------
        value : str or None
            The URL prefix template, or ``None``.
        """
        self._client_prefix = value

    def enable_colab(self):
        """
        Configure this client for use on Google Colab.

        Sets :attr:`client_host` to ``"localhost"`` and :attr:`client_port`
        to the server port so that tiles are accessible within Colab.
        """
        self.client_host = "localhost"
        self.client_port = True

    @property
    def client_base_url(self):
        """
        Return the base URL used by the client browser to access tiles.

        The URL is constructed from :attr:`client_host`, :attr:`client_port`,
        and :attr:`client_prefix`. Falls back to a relative path ``"/"`` when
        neither host nor port is configured.

        Returns
        -------
        str
            The client-facing base URL.
        """
        host = self.client_host.rstrip("/") if self.client_host is not None else None
        scheme = "http://" if host is not None and not host.startswith("http") else ""
        if self.client_port is not None and host is not None:
            base = f"{scheme}{host}:{self.client_port}"
        elif self.client_port is None and host is not None:
            base = f"{scheme}{host}"
        elif self.client_port is not None and host is None:
            base = f"http://{self.server_host}:{self.client_port}"
        else:
            base = "/"  # Use relative path
        if self.client_prefix:
            prefix = self.client_prefix
            if base.endswith("/"):
                prefix = prefix.lstrip("/")
            elif not prefix.startswith("/"):
                prefix = f"/{prefix}"
            base = f"{base}{prefix}"
        if base.startswith("/"):
            base = f"/{base.lstrip('/')}"
        return base

    def _produce_url(self, base: str):
        return add_query_parameters(base, {"filename": self.filename})

    def create_url(self, path: str, client: bool = False):
        """
        Build a full URL for the given API path.

        Parameters
        ----------
        path : str
            The relative API path (e.g., ``"api/metadata"``).
        client : bool, optional
            If ``True``, build the URL using the client-facing host and port
            instead of the server-side values. Defaults to ``False``.

        Returns
        -------
        str
            The fully-qualified URL with query parameters.
        """
        if client and (
            self.client_port is not None
            or self.client_host is not None
            or self.client_prefix is not None
        ):
            base = self.client_base_url
        else:
            base = self.server_base_url
        # Normalize the join so the result never contains "//" between host
        # and path. Starlette does not collapse "//" in request paths (unlike
        # Werkzeug), so a trailing slash on ``client_host`` or ``client_prefix``
        # would otherwise produce tile URLs that 404.
        sep = "" if base.endswith("/") else "/"
        return self._produce_url(f"{base}{sep}{path.lstrip('/')}")

    def get_tile_url(
        self,
        indexes: list[int] | None = None,
        colormap: str | Colormap | list[str] | None = None,
        vmin: float | list[float] | None = None,
        vmax: float | list[float] | None = None,
        nodata: int | float | None = None,
        client: bool = False,
        expression: str | None = None,
        stretch: str | None = None,
    ):
        """
        Get slippy maps tile URL (e.g., ``/zoom/x/y.png``).

        Parameters
        ----------
        indexes : list of int, optional
            The band(s) of the source raster to use (default if ``None`` is to
            show RGB if available). Band indexing starts at 1. This can also be
            a list of integers to set which 3 bands to use for RGB.
        colormap : str or Colormap or list of str, optional
            The name of the matplotlib colormap, a ``Colormap`` instance, or a
            list of color strings to use when plotting a single band. Default
            is greyscale.
        vmin : float or list of float, optional
            The minimum value to use when colormapping a single band.
        vmax : float or list of float, optional
            The maximum value to use when colormapping a single band.
        nodata : int or float, optional
            The value from the band to use to interpret as not valid data.
        client : bool, optional
            If ``True``, build the URL using the client-facing host and port.
            Defaults to ``False``.
        expression : str, optional
            Band math expression (e.g., ``"(b4-b1)/(b4+b1)"``).
            Mutually exclusive with ``indexes``.
        stretch : str, optional
            Image stretch mode. One of ``"none"``, ``"minmax"``,
            ``"linear"``, ``"equalize"``, ``"sqrt"``, or ``"log"``.
            When set, overrides ``vmin``/``vmax``.

        Returns
        -------
        str
            The tile URL template with ``{z}/{x}/{y}`` placeholders.
        """
        if expression and indexes is not None:
            raise ValueError("Cannot use both 'expression' and 'indexes'.")
        # First handle query parameters to check for errors
        params = {}
        if indexes is not None:
            params["indexes"] = indexes
        if colormap is not None:
            if isinstance(colormap, (Colormap, ListedColormap)):
                # Register the colormap server-side to avoid URL overflow (#231)
                if isinstance(colormap, ListedColormap):
                    c = LinearSegmentedColormap.from_list("", colormap.colors, N=256)
                else:
                    c = colormap
                cmap_data = {
                    int(k): tuple(float(x) for x in v) for k, v in enumerate(c(range(256), 1, 1))
                }
                colormap = register_colormap(cmap_data)
            elif isinstance(colormap, list):
                colormap = json.dumps(colormap)
            else:
                # make sure palette is valid
                palette_valid_or_raise(colormap)

            params["colormap"] = colormap
        if vmin is not None:
            if isinstance(vmin, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `vmin` is an iterable.")
            params["vmin"] = vmin
        if vmax is not None:
            if isinstance(vmax, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `vmax` is an iterable.")
            params["vmax"] = vmax
        if nodata is not None:
            if isinstance(nodata, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `nodata` is an iterable.")
            params["nodata"] = nodata
        if expression is not None:
            params["expression"] = expression
        if stretch is not None:
            params["stretch"] = stretch
        return add_query_parameters(
            self.create_url("api/tiles/{z}/{x}/{y}.png", client=client), params
        )

    def as_leaflet_layer(self):
        """
        Create an ipyleaflet TileLayer for this dataset.

        Returns
        -------
        ipyleaflet.TileLayer
            A tile layer that can be added to an ``ipyleaflet.Map``.
        """
        from localtileserver.widgets import get_leaflet_tile_layer

        return get_leaflet_tile_layer(self)

    def get_leaflet_map(self, add_bounds: bool = False, **kwargs):
        """
        Get an ipyleaflet Map centered and zoomed to the dataset bounds.

        Parameters
        ----------
        add_bounds : bool, optional
            If ``True``, add a WKT boundary layer to the map. Requires
            ``shapely``. Defaults to ``False``.
        **kwargs
            Additional keyword arguments passed to ``ipyleaflet.Map``.

        Returns
        -------
        ipyleaflet.Map
            A map widget centered on the dataset with the default zoom level.
        """
        m = Map(center=self.center(), zoom=self.default_zoom, **kwargs)
        if add_bounds:
            if not shapely:
                raise ImportError("Please install `shapely` to use this feature.")
            wlayer = WKTLayer(
                wkt_string=self.bounds(return_wkt=True),
                style={"dashArray": 9, "fillOpacity": 0, "weight": 1},
            )
            m.add(wlayer)
        return m

    if ipyleaflet:

        def _ipython_display_(self):
            # Deferred import: widgets.py imports from client.py (circular).
            from localtileserver.widgets import get_leaflet_tile_layer

            t = get_leaflet_tile_layer(self)
            m = self.get_leaflet_map(add_bounds=shapely)
            m.add(t)
            return _ipython_display_fn(m)


class TileClient(TilerInterface, TileServerMixin):
    """
    Tile client interface for generating and serving tiles.

    Parameters
    ----------
    source : pathlib.Path, str, Reader, DatasetReaderBase
        The source dataset to use for the tile client.
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.
    host : str
        The host address to bind the tile server to.
    client_port : int
        The port on your client browser to use for fetching tiles. This is
        useful when running in Docker and performing port forwarding.
    client_host : str
        The host on which your client browser can access the server.
    client_prefix : str
        The URL prefix used for proxied access to the tile server.
    cors_all : bool
        If ``True``, enable CORS for all origins on the tile server.
    """

    def __init__(
        self,
        source: pathlib.Path | str | rasterio.io.DatasetReaderBase,
        port: int | str = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int | None = None,
        client_host: str | None = None,
        client_prefix: str | None = None,
        cors_all: bool = False,
    ):
        TilerInterface.__init__(self, source=source)
        TileServerMixin.__init__(
            self,
            port=port,
            debug=debug,
            host=host,
            client_port=client_port,
            client_host=client_host,
            client_prefix=client_prefix,
            cors_all=cors_all,
        )


class STACClient(TileServerMixin):
    """
    Tile client for STAC (SpatioTemporal Asset Catalog) items.

    This is a separate class from ``TileClient`` rather than a unified
    client because the two are backed by fundamentally different rio-tiler
    reader types with incompatible APIs:

    - ``TileClient`` wraps ``rio_tiler.io.Reader`` and addresses data by
      **band index** (``indexes=[1, 2, 3]``).  The full rendering pipeline
      (colormap, vmin/vmax, stretch, nodata) is available.
    - ``STACClient`` wraps ``rio_tiler.io.STACReader`` and addresses data
      by **asset name** (``assets=["B04", "B03", "B02"]``).  The STAC
      tile endpoints currently pass rendering through to rio-tiler
      defaults without colormap/stretch support.

    All of ``TilerInterface``'s methods call handler functions (e.g.
    ``get_tile``, ``get_preview``) that expect a ``Reader``.  The STAC
    handler functions (``get_stac_tile``, ``get_stac_preview``) accept
    different arguments, so the two cannot share an implementation today.

    **Future improvement:** A unified ``TileClient`` could accept either
    source type and dispatch to the correct handler, exposing both
    ``indexes`` and ``assets`` parameters where appropriate.  This would
    also be the place to wire colormap/stretch/vmin/vmax support into the
    STAC rendering path (currently unsupported at the endpoint level).

    Parameters
    ----------
    url : str
        URL to a STAC item JSON document.
    assets : list of str, optional
        Default asset names to use for tiles and thumbnails.
    expression : str, optional
        Default band math expression for cross-asset computations.
    port : int or str, optional
        Port for the tile server. Defaults to an available port.
    debug : bool, optional
        Run the tile server in debug mode.
    host : str, optional
        Host address to bind the tile server to.
    client_port : int, optional
        Port used by the client browser.
    client_host : str, optional
        Host used by the client browser.
    client_prefix : str, optional
        URL prefix for proxied access.
    cors_all : bool, optional
        If ``True``, enable CORS for all origins.
    """

    def __init__(
        self,
        url: str,
        assets: list[str] | None = None,
        expression: str | None = None,
        port: int | str = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int | None = None,
        client_host: str | None = None,
        client_prefix: str | None = None,
        cors_all: bool = False,
    ):
        self.stac_url = url
        self._assets = assets
        self._expression = expression
        self._stac_reader = get_stac_reader(url)
        TileServerMixin.__init__(
            self,
            port=port,
            debug=debug,
            host=host,
            client_port=client_port,
            client_host=client_host,
            client_prefix=client_prefix,
            cors_all=cors_all,
        )

    @property
    def filename(self):
        """
        Return the STAC item URL.

        Returns
        -------
        str
            The STAC item URL.
        """
        return self.stac_url

    def _produce_url(self, base: str):
        return add_query_parameters(base, {"url": self.stac_url})

    def bounds(self):
        """
        Get the geographic bounds of the STAC item.

        Returns
        -------
        tuple of float
            A tuple of ``(south, north, west, east)`` in EPSG:4326.
        """
        # STACReader.bounds is (left, bottom, right, top) in EPSG:4326
        b = self._stac_reader.bounds
        return (b[1], b[3], b[0], b[2])

    def center(self):
        """
        Get the center of the STAC item in ``(lat, lon)`` form.

        Returns
        -------
        tuple of float
            A tuple of ``(latitude, longitude)``.
        """
        b = self.bounds()
        return (
            (b[1] - b[0]) / 2 + b[0],
            (b[3] - b[2]) / 2 + b[2],
        )

    @property
    def default_zoom(self):
        """
        Return the default zoom level for the STAC item.

        Returns
        -------
        int
            The minimum zoom level.
        """
        try:
            return self._stac_reader.minzoom
        except Exception:
            return 1

    def tile(
        self,
        z: int,
        x: int,
        y: int,
        assets: list[str] | None = None,
        expression: str | None = None,
        encoding: str = "PNG",
    ):
        """
        Generate a tile from the STAC item.

        Parameters
        ----------
        z : int
            Tile zoom level.
        x : int
            Tile column index.
        y : int
            Tile row index.
        assets : list of str, optional
            Asset names to read. Falls back to the default assets.
        expression : str, optional
            Band math expression. Falls back to the default expression.
        encoding : str, optional
            Output image format. Defaults to ``"PNG"``.

        Returns
        -------
        bytes
            The tile image as binary data.
        """
        encoding = format_to_encoding(encoding)
        return get_stac_tile(
            self._stac_reader,
            z,
            x,
            y,
            assets=assets or self._assets,
            expression=expression or self._expression,
            img_format=encoding,
        )

    def thumbnail(
        self,
        assets: list[str] | None = None,
        expression: str | None = None,
        encoding: str = "PNG",
        max_size: int = 512,
        output_path: pathlib.Path | None = None,
    ):
        """
        Generate a thumbnail preview of the STAC item.

        Parameters
        ----------
        assets : list of str, optional
            Asset names to read. Falls back to the default assets.
        expression : str, optional
            Band math expression. Falls back to the default expression.
        encoding : str, optional
            Output image format. Defaults to ``"PNG"``.
        max_size : int, optional
            Maximum dimension of the thumbnail. Defaults to 512.
        output_path : pathlib.Path, optional
            If provided, write the image to this file path.

        Returns
        -------
        bytes
            The thumbnail image as binary data.
        """
        encoding = format_to_encoding(encoding)
        result = get_stac_preview(
            self._stac_reader,
            assets=assets or self._assets,
            expression=expression or self._expression,
            img_format=encoding,
            max_size=max_size,
        )
        if output_path:
            with open(output_path, "wb") as f:
                f.write(result)
        return result

    def stac_info(self, assets: list[str] | None = None):
        """
        Get STAC item metadata.

        Parameters
        ----------
        assets : list of str, optional
            Asset names to query. Falls back to the default assets.

        Returns
        -------
        dict
            Dictionary mapping asset names to their metadata.
        """
        return get_stac_info(self._stac_reader, assets=assets or self._assets)

    def statistics(self, assets: list[str] | None = None, **kwargs):
        """
        Get per-asset/band statistics.

        Parameters
        ----------
        assets : list of str, optional
            Asset names to compute statistics for. Falls back to the
            default assets.
        **kwargs
            Additional keyword arguments passed to the underlying
            statistics function.

        Returns
        -------
        dict
            Per-asset/band statistics.
        """
        return get_stac_statistics(self._stac_reader, assets=assets or self._assets, **kwargs)

    def get_tile_url(
        self,
        assets: list[str] | None = None,
        expression: str | None = None,
        client: bool = False,
        **kwargs,
    ):
        """
        Get slippy maps tile URL for the STAC item.

        Parameters
        ----------
        assets : list of str, optional
            Asset names to include. Falls back to the default assets.
        expression : str, optional
            Band math expression. Falls back to the default expression.
        client : bool, optional
            If ``True``, build the URL using the client-facing host/port.
        **kwargs
            Accepted for compatibility with widget helpers; ignored.

        Returns
        -------
        str
            The tile URL template with ``{z}/{x}/{y}`` placeholders.
        """
        params = {}
        assets = assets or self._assets
        expression = expression or self._expression
        if assets is not None:
            params["assets"] = ",".join(assets) if isinstance(assets, list) else assets
        if expression is not None:
            params["expression"] = expression
        return add_query_parameters(
            self.create_url("api/stac/tiles/{z}/{x}/{y}.png", client=client), params
        )

    def _repr_png_(self):
        """Return a PNG thumbnail for IPython/Jupyter rich display."""
        return self.thumbnail(encoding="png")


def get_or_create_tile_client(
    source: pathlib.Path | str | TileClient | rasterio.io.DatasetReaderBase,
    port: int | str = "default",
    debug: bool = False,
):
    """
    Get an existing TileClient or create a new one from a source.

    Parameters
    ----------
    source : pathlib.Path, str, TileClient, or rasterio.io.DatasetReaderBase
        The raster source. If already a ``TileClient``, it is used directly.
        Otherwise, a new ``TileClient`` is created.
    port : int or str, optional
        The port on your host machine to use for the tile server. Defaults to
        ``"default"`` which selects an available port.
    debug : bool, optional
        Run the tile server in debug mode. Defaults to ``False``.

    Returns
    -------
    source : TileClient
        The tile client instance.
    _internally_created : bool
        ``True`` if a new ``TileClient`` was created internally, ``False``
        if the provided ``source`` was already a ``TileClient``.

    Notes
    -----
    There should eventually be a check to see if a TileClient instance exists
    for the given filename. For now, it is not a big deal because the default
    is for all TileClients to share a single server.
    """
    _internally_created = False
    # STACClient is already a running client; pass it through directly
    if isinstance(source, STACClient):
        return source, False
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
