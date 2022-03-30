![tile-diagram](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/tile-diagram.gif)

# 🌐 Local Tile Server for Geospatial Rasters

[![codecov](https://codecov.io/gh/banesullivan/localtileserver/branch/main/graph/badge.svg?token=S0HQ64FW8G)](https://codecov.io/gh/banesullivan/localtileserver)
[![PyPI](https://img.shields.io/pypi/v/localtileserver.svg?logo=python&logoColor=white)](https://pypi.org/project/localtileserver/)
[![conda](https://img.shields.io/conda/vn/conda-forge/localtileserver.svg?logo=conda-forge&logoColor=white)](https://anaconda.org/conda-forge/localtileserver)

*Need to visualize a rather large (gigabytes) raster you have locally?* **This is for you.**

A Flask application for serving tiles from large raster files in
the [Slippy Maps standard](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
(i.e., `/zoom/x/y.png`)

Launch a [demo](https://github.com/banesullivan/localtileserver-demo) on MyBinder [![MyBinder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/banesullivan/localtileserver-demo/HEAD)

Documentation: https://localtileserver.banesullivan.com/


## 🌟 Highlights

- Launch a tile server for large geospatial images
- View local or remote* raster files with `ipyleaflet` or `folium` in Jupyter
- View rasters with CesiumJS with the built-in Flask web application
- Extract regions of interest (ROIs) interactively
- Use the example datasets to generate Digital Elevation Models

**remote raster files should be pre-tiled Cloud Optimized GeoTiffs*

## 🚀 Usage

Usage details and examples can be found in the documentation: https://localtileserver.banesullivan.com/

The following is a minimal example to visualize a local raster file with
`ipyleaflet`:

```py
from localtileserver import get_leaflet_tile_layer, TileClient
from ipyleaflet import Map

# First, create a tile server from local raster file
tile_client = TileClient('path/to/geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_client)

m = Map(center=tile_client.center(), zoom=6)
m.add_layer(t)
m
```

![ipyleaflet](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet.png)

## ℹ️ Overview

This is a Flask application (blueprint) for serving tiles of large images.
The `TileClient` class can be used to to launch a tile server in a background
thread which will serve raster imagery to a viewer (see `ipyleaflet` and
`folium` Jupyter notebook examples below).

This tile server can efficiently deliver varying levels of detail of your
raster imagery to your viewer; it helps to have pre-tiled, Cloud Optimized
GeoTIFFs (COG), but no wories if not as the backing libraries,
[`large_image`](https://github.com/girder/large_image),
will tile and cache for you when opening the raster.

There is an included, standalone web viewer leveraging
[CesiumJS](https://cesium.com/platform/cesiumjs/) and [GeoJS](https://opengeoscience.github.io/geojs/).
You can use the web viewer to select and extract regions of interest from rasters.

**Disclaimer**: This is a hobby project and I am doing my best to make it
more stable/robust. Things might break between minor releases (I use the
`major.minor.patch` versioning scheme).


## ⬇️ Installation

Get started with `localtileserver` to view rasters locally in Jupyter or
deploy in your own Flask application.

### 🐍 Installing with `conda`

Conda makes managing `localtileserver`'s dependencies across platforms quite
easy and this is the recommended method to install:

```bash
conda install -c conda-forge localtileserver
```

### 🎡 Installing with `pip`

If you prefer pip, and know how to install GDAL on your system, then you can
install from PyPI: https://pypi.org/project/localtileserver/

```
pip install localtileserver
```

#### 📝 A Brief Note on Installing GDAL

GDAL can be a pain in the 🍑 to install, so you may want to handle GDAL
before installing `localtileserver` when using `pip`.

If on linux, I highly recommend using the [large_image_wheels](https://github.com/girder/large_image_wheels) from Kitware.

```
pip install --find-links=https://girder.github.io/large_image_wheels --no-cache GDAL
```

## 💭 Feedback

Please share your thoughts and questions on the [Discussions](https://github.com/banesullivan/localtileserver/discussions) board.
If you would like to report any bugs or make feature requests, please open an issue.

If filing a bug report, please share a scooby `Report`:

```py
import localtileserver
print(localtileserver.Report())
```
