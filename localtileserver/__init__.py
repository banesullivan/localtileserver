"""
``localtileserver`` — serve geospatial raster tiles from Python.

A background tile server (FastAPI + rio-tiler) that streams Slippy-map
tiles to ``ipyleaflet`` / ``folium`` / CesiumJS / any HTTP client, from:

- local raster files and remote Cloud Optimized GeoTIFFs
- STAC items (via :class:`STACClient`)
- xarray DataArrays (NetCDF, Zarr, ...)
- virtual mosaics of many rasters

The usual entrypoint is :func:`open`, which returns a
:class:`TileClient` ready for use with :func:`get_leaflet_tile_layer`,
:func:`get_folium_tile_layer`, and the other helpers.
"""

try:
    from localtileserver._version import version as __version__
except ImportError:  # Only happens if not properly installed.
    __version__ = "unknown"

from localtileserver._jupyter_loopback_bridge import enable_jupyter_loopback
from localtileserver.client import STACClient, TileClient, get_or_create_tile_client
from localtileserver.helpers import hillshade, parse_shapely, polygon_to_geojson, save_new_raster
from localtileserver.io import open
from localtileserver.report import Report
from localtileserver.tiler import get_cache_dir, make_vsi, purge_cache
from localtileserver.validate import validate_cog
from localtileserver.widgets import (
    LocalTileServerLayerMixin,
    get_folium_tile_layer,
    get_leaflet_tile_layer,
)
