import logging
import pathlib
from typing import List, Union

import requests

from localtileserver.tileserver import get_clean_filename, palette_valid_or_raise
from localtileserver.utilities import add_query_parameters, save_file_from_request

DEMO_REMOTE_TILE_SERVER = "https://localtileserver-demo.herokuapp.com/"
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
    def host(self):
        raise NotImplementedError

    @property
    def base_url(self):
        raise NotImplementedError

    def _produce_url(self, base: str):
        return add_query_parameters(base, {"filename": self._filename})

    def create_url(self, path: str):
        return self._produce_url(f"{self.base_url}/{path.lstrip('/')}")

    def get_tile_url(
        self,
        projection: str = "EPSG:3857",
        band: Union[int, List[int]] = None,
        palette: Union[str, List[str]] = None,
        vmin: Union[Union[float, int], List[Union[float, int]]] = None,
        vmax: Union[Union[float, int], List[Union[float, int]]] = None,
        nodata: Union[Union[float, int], List[Union[float, int]]] = None,
        grid: bool = False,
    ):
        """

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
        vmin : float
            The minimum value to use when colormapping the palette when plotting
            a single band.
        vmax : float
            The maximized value to use when colormapping the palette when plotting
            a single band.
        nodata : float
            The value from the band to use to interpret as not valid data.
        grid : bool
            Show the outline of each tile. This is useful when debugging your
            tile viewer.

        """
        # First handle query parameters to check for errors
        params = {}
        if band is not None:
            params["band"] = band
        if palette is not None:
            # make sure palette is valid
            palette_valid_or_raise(palette)
            params["palette"] = palette
        if vmin is not None:
            params["min"] = vmin
        if vmax is not None:
            params["max"] = vmax
        if nodata is not None:
            params["nodata"] = nodata
        if projection is not None:
            params["projection"] = projection
        if grid:
            params["grid"] = True
        return add_query_parameters(self.create_url("tiles/{z}/{x}/{y}.png"), params)

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
        path = f"/world/region.tif?units={units}&encoding={encoding}&left={left}&right={right}&bottom={bottom}&top={top}"
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
        """Extract ROI in world coordinates."""
        path = f"/pixel/region.tif?encoding={encoding}&left={left}&right={right}&bottom={bottom}&top={top}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        return save_file_from_request(r, output_path)

    def metadata(self):
        r = requests.get(self.create_url("/metadata"))
        r.raise_for_status()
        return r.json()

    def bounds(self, projection: str = "EPSG:4326"):
        """Get bounds in form of (ymin, ymax, xmin, xmax)."""
        r = requests.get(self.create_url(f"/bounds?projection={projection}"))
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
        output_path: pathlib.Path = None,
    ):
        params = {}
        if band is not None:
            params["band"] = band
        if palette is not None:
            # make sure palette is valid
            palette_valid_or_raise(palette)
            params["palette"] = palette
        if vmin is not None:
            params["min"] = vmin
        if vmax is not None:
            params["max"] = vmax
        if nodata is not None:
            params["nodata"] = nodata
        url = add_query_parameters(self.create_url("thumbnail"), params)
        r = requests.get(url)
        r.raise_for_status()
        return save_file_from_request(r, output_path)


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
    def host(self):
        return self._host

    @host.setter
    def host(self, host):
        self._host = host

    @property
    def base_url(self):
        return self.host
