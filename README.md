### 🚀 Support This Project

If localtileserver saves you time, powers your work, or you need direct help, please consider supporting the project and my efforts:

[![Sponsor](https://img.shields.io/badge/Sponsor%20Bane%20Sullivan-🚀-green?style=for-the-badge)](https://github.com/sponsors/banesullivan)

![tile-diagram](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/oam-tiles.jpg)

# 🌐 Local Tile Server for Geospatial Rasters

[![codecov](https://codecov.io/gh/banesullivan/localtileserver/branch/main/graph/badge.svg?token=S0HQ64FW8G)](https://codecov.io/gh/banesullivan/localtileserver)
[![PyPI](https://img.shields.io/pypi/v/localtileserver.svg?logo=python&logoColor=white)](https://pypi.org/project/localtileserver/)
[![conda](https://img.shields.io/conda/vn/conda-forge/localtileserver.svg?logo=conda-forge&logoColor=white)](https://anaconda.org/conda-forge/localtileserver)

_Need to visualize a rather large (gigabytes+) raster?_ **This is for you.**

A Python package for serving tiles from large raster files in
the [Slippy Maps standard](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
(i.e., `/zoom/x/y.png`) for visualization in Jupyter with `ipyleaflet` or `folium`.

Launch a [demo](https://github.com/banesullivan/localtileserver-demo) on MyBinder [![MyBinder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/banesullivan/localtileserver-demo/HEAD)

Documentation: https://localtileserver.banesullivan.com/

Built on [rio-tiler](https://github.com/cogeotiff/rio-tiler) and [FastAPI](https://fastapi.tiangolo.com/)

## 🌟 Highlights

- Launch a tile server for large geospatial images
- View local or remote raster files with `ipyleaflet` or `folium` in Jupyter
- Band math expressions for on-the-fly computed imagery (e.g., NDVI)
- Per-band statistics and multiple image stretch modes
- Multiple output formats: PNG, JPEG, WebP, GeoTIFF, NPY
- Spatial subsetting via bounding box crops and GeoJSON masks
- [STAC](https://stacspec.org/) item support for multi-asset catalogs
- [Xarray](https://xarray.dev/) DataArray tile serving (NetCDF, Zarr, etc.)
- Virtual mosaics from multiple raster files
- View rasters with CesiumJS with the built-in web application
- Full REST API powered by FastAPI with auto-generated OpenAPI docs

## 🚀 Usage

Usage details and examples can be found in the documentation: https://localtileserver.banesullivan.com/

The following is a minimal example to visualize a local raster file with
`ipyleaflet`:

```py
from localtileserver import get_leaflet_tile_layer, TileClient
from ipyleaflet import Map

# First, create a tile server from local raster file
client = TileClient('path/to/geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(client)

m = Map(center=client.center(), zoom=client.default_zoom)
m.add(t)
m
```

![ipyleaflet](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet.png)

### Band Math Expressions

Compute derived imagery on the fly using band math expressions:

```py
client = TileClient('path/to/multispectral.tif')

# NDVI: (NIR - Red) / (NIR + Red) where NIR=b4, Red=b1
t = get_leaflet_tile_layer(client, expression='(b4-b1)/(b4+b1)',
                           vmin=-1, vmax=1, colormap='RdYlGn')
```

### STAC Support

Visualize assets from STAC catalogs:

```py
import requests

# Fetch tiles from a STAC item's assets
resp = requests.get('http://localhost:PORT/api/stac/tiles/10/512/512.png',
                    params={'url': 'https://example.com/stac/item.json',
                            'assets': 'visual'})
```

### Xarray DataArrays

Serve tiles directly from xarray DataArrays (NetCDF, Zarr, etc.):

```py
import xarray as xr

ds = xr.open_dataset('temperature.nc')
da = ds['temperature']
da = da.rio.write_crs('EPSG:4326')

# Register and serve tiles through the REST API
```

## ℹ️ Overview

The `TileClient` class can be used to launch a tile server in a background
thread which will serve raster imagery to a viewer (usually `ipyleaflet` or
`folium` in Jupyter notebooks).

This tile server can efficiently deliver varying resolutions of your
raster imagery to your viewer; it helps to have pre-tiled,
[Cloud Optimized GeoTIFFs (COGs)](https://www.cogeo.org/).

There is an included, standalone web viewer leveraging
[CesiumJS](https://cesium.com/platform/cesiumjs/).

### REST API

The server exposes a comprehensive REST API built on FastAPI:

| Endpoint                                  | Description             |
| ----------------------------------------- | ----------------------- |
| `GET /api/tiles/{z}/{x}/{y}.{fmt}`        | Raster tiles            |
| `GET /api/thumbnail.{fmt}`                | Thumbnail preview       |
| `GET /api/metadata`                       | Raster metadata         |
| `GET /api/bounds`                         | Geographic bounds       |
| `GET /api/statistics`                     | Per-band statistics     |
| `GET /api/part.{fmt}`                     | Bounding box crop       |
| `POST /api/feature.{fmt}`                 | GeoJSON mask extraction |
| `GET /api/stac/tiles/{z}/{x}/{y}.{fmt}`   | STAC item tiles         |
| `GET /api/xarray/tiles/{z}/{x}/{y}.{fmt}` | Xarray DataArray tiles  |
| `GET /api/mosaic/tiles/{z}/{x}/{y}.{fmt}` | Mosaic tiles            |
| `GET /swagger/`                           | Interactive API docs    |

All tile/thumbnail endpoints support `expression`, `stretch`, `indexes`, `colormap`, `vmin`, `vmax`, and `nodata` query parameters.

## ⬇️ Installation

Get started with `localtileserver` to view rasters in Jupyter or deploy as your
own FastAPI application.

### 🐍 Installing with `conda`

Conda makes managing `localtileserver`'s dependencies across platforms quite
easy and this is the recommended method to install:

```bash
conda install -c conda-forge localtileserver
```

### 🎡 Installing with `pip`

If you prefer pip, then you can install from PyPI: https://pypi.org/project/localtileserver/

```
pip install localtileserver
```

### Optional Dependencies

For xarray/DataArray support:

```
pip install localtileserver[xarray]
```

For Jupyter widget integration:

```
pip install localtileserver[jupyter]
```

For additional colormaps:

```
pip install localtileserver[colormaps]
```

## 💭 Feedback

Please share your thoughts and questions on the [Discussions](https://github.com/banesullivan/localtileserver/discussions) board.
If you would like to report any bugs or make feature requests, please open an issue.

If filing a bug report, please share a scooby `Report`:

```py
import localtileserver
print(localtileserver.Report())
```
