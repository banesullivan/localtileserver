# flake8: noqa: W503
import base64
from functools import wraps
import json
import logging
import pathlib
from typing import List, Union

import requests

from localtileserver.configure import get_default_client_params
from localtileserver.server import ServerManager, launch_server
from localtileserver.tileserver import get_building_docs, get_clean_filename, palette_valid_or_raise
from localtileserver.utilities import add_query_parameters, save_file_from_request

BUILDING_DOCS = get_building_docs()
DEMO_REMOTE_TILE_SERVER = "https://tileserver.banesullivan.com/"
logger = logging.getLogger(__name__)


class BaseTileClient:
    """Connect to a localtileserver instance.

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

    @property
    def filename(self):
        return self._filename

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

    def create_url(self, path: str):
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
            return {"style": base64.urlsafe_b64encode(json.dumps(style).encode()).decode()}
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
            params["min"] = vmin
        if vmax is not None:
            params["max"] = vmax
        if nodata is not None:
            params["nodata"] = nodata
        if scheme is not None:
            params["scheme"] = scheme
        if n_colors:
            params["n_colors"] = n_colors
        return params

    def get_tile_url_params(
        self,
        projection: str = "EPSG:3857",
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
        if projection is not None:
            params["projection"] = projection
        if grid:
            params["grid"] = True
        return params

    @wraps(get_tile_url_params)
    def get_tile_url(self, *args, **kwargs):
        params = self.get_tile_url_params(*args, **kwargs)
        return add_query_parameters(self.create_url("api/tiles/{z}/{x}/{y}.png"), params)

    def extract_roi(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        units: str = "EPSG:4326",
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
    ):
        """Extract ROI in world coordinates."""
        path = f"api/world/region.tif?units={units}&encoding={encoding}&left={left}&right={right}&bottom={bottom}&top={top}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        return save_file_from_request(r, output_path)

    def extract_roi_pixel(
        self,
        left: int,
        right: int,
        bottom: int,
        top: int,
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
    ):
        """Extract ROI in pixel coordinates."""
        path = f"/api/pixel/region.tif?encoding={encoding}&left={left}&right={right}&bottom={bottom}&top={top}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        return save_file_from_request(r, output_path)

    def metadata(self):
        r = requests.get(self.create_url("/api/metadata"))
        r.raise_for_status()
        return r.json()

    def bounds(self, projection: str = "EPSG:4326"):
        """Get bounds in form of (ymin, ymax, xmin, xmax)."""
        r = requests.get(self.create_url(f"/api/bounds?units={projection}"))
        r.raise_for_status()
        bounds = r.json()
        return (bounds["ymin"], bounds["ymax"], bounds["xmin"], bounds["xmax"])

    def center(self, projection: str = "EPSG:4326"):
        """Get center in the form of (y <lat>, x <lon>)."""
        bounds = self.bounds(projection=projection)
        return (
            (bounds[1] - bounds[0]) / 2 + bounds[0],
            (bounds[3] - bounds[2]) / 2 + bounds[2],
        )

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
    ):
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
        url = add_query_parameters(self.create_url("api/thumbnail.png"), params)
        r = requests.get(url)
        r.raise_for_status()
        return save_file_from_request(r, output_path)

    def pixel(self, y: float, x: float, units: str = "pixels", projection: str = None):
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
        params = {}
        params["x"] = x
        params["y"] = y
        params["units"] = units
        if projection is not None:
            params["projection"] = projection
        url = add_query_parameters(self.create_url("api/pixel"), params)
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def histogram(self, bins: int = 256, density: bool = False):
        """Get a histoogram for each band."""
        params = {}
        params["density"] = density
        params["bins"] = bins
        url = add_query_parameters(self.create_url("api/histogram"), params)
        r = requests.get(url)
        r.raise_for_status()
        return r.json()


class RemoteTileClient(BaseTileClient):
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
        host: str = None,
    ):
        super().__init__(filename=filename)
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


class TileClient(BaseTileClient):
    """Serve tiles from a local raster file in a background thread.

    Parameters
    ----------
    path : pathlib.Path, str
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
        filename: Union[pathlib.Path, str],
        port: Union[int, str] = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int = None,
        client_host: str = None,
        client_prefix: str = None,
    ):
        super().__init__(filename)
        self._key = launch_server(port, debug, host=host)
        # Store actual port just in case
        self._port = ServerManager.get_server(self._key).srv.port
        client_host, client_port, client_prefix = get_default_client_params(
            client_host, client_port, client_prefix
        )
        self._client_host = client_host
        self._client_port = client_port
        self._client_prefix = client_prefix
        if BUILDING_DOCS and not client_host:
            self._client_host = DEMO_REMOTE_TILE_SERVER

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
    def get_tile_url(self, *args, client=False, **kwargs):
        params = self.get_tile_url_params(*args, **kwargs)
        return add_query_parameters(
            self.create_url("api/tiles/{z}/{x}/{y}.png", client=client), params
        )


def get_or_create_tile_client(
    source: Union[pathlib.Path, str, TileClient],
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
    if isinstance(source, RemoteTileClient):
        return source, False
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
