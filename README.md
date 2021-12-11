# 🌐 Local Tile Server for Geospatial Rasters

[![codecov](https://codecov.io/gh/banesullivan/localtileserver/branch/main/graph/badge.svg?token=S0HQ64FW8G)](https://codecov.io/gh/banesullivan/localtileserver)
[![PyPI](https://img.shields.io/pypi/v/localtileserver.svg?logo=python&logoColor=white)](https://pypi.org/project/localtileserver/)
[![conda](https://img.shields.io/conda/vn/conda-forge/localtileserver.svg?logo=conda-forge&logoColor=white)](https://anaconda.org/conda-forge/localtileserver)

*Need to visualize a rather large (gigabytes) raster you have locally?* **This is for you.**

A Flask application for serving tiles from large raster files in
the [Slippy Maps standard](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
(i.e., `/zoom/x/y.png`)

![tile-diagram](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/tile-diagram.gif)


## 🌟 Highlights

- Create a local tile server for large geospatial images
- View local or remote* raster files with `ipyleaflet` or `folium`
- Extract regions of interest (ROIs) interactively
- Use the example datasets to generate Digital Elevation Models
- Visualize rasters with the included CesiumJS web viewer

**remote raster files should be pre-tiled Cloud Optimized GeoTiffs*

## ℹ️ Overview

Under the hood, this uses [`large_image`](https://github.com/girder/large_image)
to launch a tile server in a background thread which will serve raster imagery
to a tile viewer (see `ipyleaflet` and `folium` examples below).
This tile server can efficiently deliver varying levels of detail of your
raster imagery to your viewer; it helps to have pre-tiled, Cloud Optimized
GeoTIFFs (COG), but no wories if not as `large_image` will tile and cache for
you when opening the raster.

There is an included, standalone web viewer leveraging
[CesiumJS](https://cesium.com/platform/cesiumjs/) and [GeoJS](https://opengeoscience.github.io/geojs/).
You can use the web viewer to select and extract regions of interest from rasters.

**Disclaimer**: I put this together over a weekend and I'm definitely going to
change a few things moving forward to make it more stable/robust. This means
that things will most likely break between minor releases (I use the
`major.minor.patch` versioning scheme).


## ⬇️ Installation


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

## 🚀 Usage

### 🍃 `ipyleaflet` Tile Layers

The `TileClient` class is a nifty tool to launch a tile server as a background
thread to serve image tiles from any raster file on your local file system.
Additionally, it can be used in conjunction with the `get_leaflet_tile_layer`
utility to create an `ipyleaflet.TileLayer` for interactive visualization in
a Jupyter notebook. Here is an example:


```py
from localtileserver import get_leaflet_tile_layer, TileClient
from ipyleaflet import Map

# First, create a tile server from local raster file
tile_client = TileClient('~/Desktop/TC_NG_SFBay_US_Geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_client)

# Create ipyleaflet map, add tile layer, and display
m = Map(center=tile_client.center())
m.add_layer(t)
m
```

![ipyleaflet](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet.png)

#### 🥓 Two Rasters at Once

```py
from localtileserver import get_leaflet_tile_layer
from ipyleaflet import Map, ScaleControl, FullScreenControl, SplitMapControl

# Create 2 tile layers from 2 separate raster files
l = get_leaflet_tile_layer('~/Desktop/TC_NG_SFBay_US_Geo.tif',
                           band=1, palette='viridis', vmin=50, vmax=200)
r = get_leaflet_tile_layer('~/Desktop/small.tif',
                           band=2, palette='plasma', vmin=0, vmax=150)

# Make the ipyleaflet map
m = Map(center=(37.7249511580583, -122.27230466902257), zoom=9)
control = SplitMapControl(left_layer=l, right_layer=r)
m.add_control(control)
m.add_control(ScaleControl(position='bottomleft'))
m.add_control(FullScreenControl())
m
```

![ipyleaflet-double](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet.gif)


#### 🧮 Controlling the RGB Bands

The `ipyleaflet` and `folium` tile layer utilities support setting which bands
to view as the RGB channels. To set the RGB bands, pass a length three list
of the band indices to the `band` argument.

Here is an example where I create two tile layers from the same raster but
viewing a different set of bands:

```py
from localtileserver import get_leaflet_tile_layer, TileClient
from ipyleaflet import Map, ScaleControl, FullScreenControl, SplitMapControl

# First, create a tile server from local raster file
tile_client = TileClient('landsat.tif')

# Create 2 tile layers from same raster viewing different bands
l = get_leaflet_tile_layer(tile_client, band=[7, 5, 4])
r = get_leaflet_tile_layer(tile_client, band=[5, 3, 2])

# Make the ipyleaflet map
m = Map(center=tile_client.center(), zoom=12)
control = SplitMapControl(left_layer=l, right_layer=r)
m.add_control(control)
m.add_control(ScaleControl(position='bottomleft'))
m.add_control(FullScreenControl())
m
```

![ipyleaflet-multi-bands](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet-multi-bands.png)


#### 🎯 Using `ipyleaflet` for ROI Extraction

I have included the `get_leaflet_roi_controls` utility to create some leaflet
UI controls for extracting regions of interest from a tile client. You can
use it as follows and then draw a polygon and click the "Extract ROI" button.

The outputs are save in your working directory by default (next to the Jupyter notebook).

```py
from localtileserver import get_leaflet_tile_layer, get_leaflet_roi_controls
from localtileserver import TileClient
from ipyleaflet import Map

# First, create a tile server from local raster file
tile_client = TileClient('~/Desktop/TC_NG_SFBay_US_Geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_client)

# Create ipyleaflet controls to extract an ROI
draw_control, roi_control = get_leaflet_roi_controls(tile_client)

# Create ipyleaflet map, add layers, add controls, and display
m = Map(center=(37.7249511580583, -122.27230466902257), zoom=9)
m.add_layer(t)
m.add_control(draw_control)
m.add_control(roi_control)
m
```

![ipyleaflet-draw-roi](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet-draw-roi.png)


### 🌳 `folium` Tile Layers

Similarly to the support provided for `ipyleaflet`, I have included a utility
to generate a [`folium.TileLayer`](https://python-visualization.github.io/folium/modules.html#folium.raster_layers.TileLayer)
with `get_folium_tile_layer`. Here is an example with almost the exact same
code as the `ipyleaflet` example, just note that `Map` is imported from
`folium` and we use `add_child` instead of `add_layer`:


```py
from localtileserver import get_folium_tile_layer
from localtileserver import TileClient
from folium import Map

# First, create a tile server from local raster file
tile_client = TileClient('~/Desktop/TC_NG_SFBay_US_Geo.tif')

# Create folium tile layer from that server
t = get_folium_tile_layer(tile_client)

m = Map(location=tile_client.center())
m.add_child(t)
m
```

![folium](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/folium.png)


### ☁️ Remote Cloud Optimized GeoTiffs (COGs)

While `localtileserver` is intended to be used only with raster files existing
on your local filesystem, there is support for URL files through GDAL's
[Virtual Storage Interface](https://gdal.org/user/virtual_file_systems.html).
Simply pass your `http<s>://` or `s3://` URL to the `TileClient`. This will
work quite well for pre-tiled Cloud Optimized GeoTiffs, but I do not recommend
doing this with non-tiled raster formats.

For example, the raster at the url below is ~3GiB but because it is pre-tiled,
we can view tiles of the remote file very efficiently in a Jupyter notebook.

```py
from localtileserver import get_folium_tile_layer
from localtileserver import TileClient
from folium import Map

url = 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'

# First, create a tile server from local raster file
tile_client = TileClient(url)

# Create folium tile layer from that server
t = get_folium_tile_layer(tile_client)

m = Map(location=tile_client.center())
m.add_child(t)
m
```

![vsi](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/vsi-raster.png)

Note that the Virtual Storage Interface is a complex API, and `TileClient`
currently only handles `vsis3` and `vsicurl`. If you need a different VFS
mechanism, simply create your `/vsi` path and pass that to `TileClient`.

### 🗺️ Example Datasets

A few example datasets are included with `localtileserver`. A particularly
useful one has global elevation data which you can use to create high resolution Digital Elevation Models (DEMs) of a local region.

```py
from localtileserver import get_leaflet_tile_layer, get_leaflet_roi_controls, examples
from ipyleaflet import Map

# Load example tile layer from publicly available DEM source
tile_client = examples.get_elevation()

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_client,
                           band=1, vmin=-500, vmax=5000,
                           palette='plasma',
                           opacity=0.75)

# Create ipyleaflet controls to extract an ROI
draw_control, roi_control = get_leaflet_roi_controls(tile_client)

m = Map(zoom=2)
m.add_layer(t)
m.add_control(draw_control)
m.add_control(roi_control)
m
```

![elevation](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/elevation.png)


Then you can follow the same routine as described above to extract an ROI.

I zoomed in over Golden, Colorado and drew a polygon of the extent of the DEM I would like to create:

![golden](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/golden-roi.png)

And perform the extraction:

```py

roi_path = '...'  # Look in your working directory

r = get_leaflet_tile_layer(roi_path, band=1,
                           palette='plasma', opacity=0.75)

m2 = Map(
        center=(39.763427033262175, -105.20614908076823),
        zoom=12,
       )
m2.add_layer(r)
m2
```

![golden-dem](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/golden-dem.png)

Here is another example with the Virtual Earth satellite imagery

```py
from localtileserver import get_leaflet_tile_layer, examples
from ipyleaflet import Map

# Load example tile layer from publicly available imagery
tile_client = examples.get_virtual_earth()

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_client, opacity=1)

m = Map(center=(39.751343612695145, -105.22181306125279), zoom=18)
m.add_layer(t)
m
```

![kafadar](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/kafadar.png)


### 🖥️ Local Web Application

Launch the tileserver from the commandline to use the included web application where you can view the raster and extract regions of interest.

```bash
python -m localtileserver path/to/raster.tif
```

![cesium-viewer](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/cesium-viewer.png)

You can use the web viewer to extract regions of interest:

![webviewer-roi](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/webviewer-roi.gif)


You can also launch the web viewer with any of the available example datasets:

```py
python -m localtileserver dem
```

Available choices are:

- `dem` or `elevation`: global elevation dataset
- `blue_marble`: Blue Marble satellite imagery
- `virtual_earth`: Microsoft's satellite/aerial imagery
- `arcgis`: ArcGIS World Street Map
- `bahamas`: Sample raster over the Bahamas


### 🗒️ Usage Notes

- `get_leaflet_tile_layer` accepts either an existing `TileClient` or a
path from which to create a `TileClient` under the hood.
- The color palette choices come from [`palettable`](https://jiffyclub.github.io/palettable/).
- If matplotlib is installed, any matplotlib colormap name cane be used a palette choice


### 🧬 Using the Flask Blueprint

Under the hood, `localtileserver` is a basic Flask Blueprint that can be easily
incorporated into any Flask application. To utilize in your own application:

```py
from flask import Flask
from localtileserver.tileserver.blueprint import cache, tileserver

app = Flask(__name__)
cache.init_app(app)
app.register_blueprint(tileserver, url_prefix='/')
```

There is an example Flask application and deployment in [`banesullivan/remotetileserver`](https://github.com/banesullivan/remotetileserver)
