# 🌐 Local Tile Server for Geospatial Rasters

[![PyPI](https://img.shields.io/pypi/v/flask-tileserver.svg?logo=python&logoColor=white)](https://pypi.org/project/flask-tileserver/)
[![codecov](https://codecov.io/gh/banesullivan/flask-tileserver/branch/main/graph/badge.svg?token=S0HQ64FW8G)](https://codecov.io/gh/banesullivan/flask-tileserver)

*Need to visualize a rather large raster (gigabytes) you have locally?* **This is for you.**

A Flask application for serving tiles from large raster files in
the [Slippy Maps standard](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
(i.e., `/zoom/x/y.png`)

![tile-diagram](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/tile-diagram.png)


## 🌟 Highlights

- Create a local tile server for large geospatial images
- Extract regions of interest (ROIs) interactively
- View local raster files with `ipyleaflet`

Under the hood, this uses [`large_image`](https://github.com/girder/large_image)
to launch a tile server in a background thread which will serve raster imagery
to a tile viewer (see `ipyleaflet` examples below).
This tile server can efficiently deliver varying levels of detail of your
raster imagery to your viewer; it helps to have pre-tiled, Cloud Optimized
GeoTIFFs (COG), but no wories if not as `large_image` will tile and cache for
you when opening the raster.

There is an included, standalone web viewer leveraging
[GeoJS](https://opengeoscience.github.io/geojs/). You can use the web viewer
to select and extract regions of interest from rasters.

## ⬇️ Installation

Install from PyPI: https://pypi.org/project/flask-tileserver/

```
pip install flask-tileserver
```

### 📝 A Brief Note on Installing GDAL

GDAL can be a pain in the 🍑 to install, and you may want to handle GDAL
before installing `flask-tileserver`.

If on linux, I highly recommend using the [large_image_wheels](https://github.com/girder/large_image_wheels) from Kitware.

```
pip install --find-links=https://girder.github.io/large_image_wheels --no-cache GDAL
```

Otherwise, I recommend using `conda`:

```
conda install -c conda-forge GDAL
```

## 💭 Feedback

Please share your thoughts and questions on the [Discussions](https://github.com/banesullivan/flask-tileserver/discussions) board.
If you would like to report any bugs or make feature requests, please open an issue.

If filing a bug report, please share a scooby `Report`:

```py
import tileserver
print(tileserver.Report())
```

## 🚀 Usage

### 🍃 `ipyleaflet` Tile Layers

There are utilities included here for launching a tile server as a background thread to serve image tiles from any raster file on your
local file system. Further, I have included a utility for
automatically launching a tile server and creating an
`ipyleaflet.TileLayer`. Here is an example:


```py
from tileserver import get_leaflet_tile_layer, TileServer
from ipyleaflet import Map

# First, create a tile server from local raster file
tile_server = TileServer('~/Desktop/TC_NG_SFBay_US_Geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_server)

# Create ipyleaflet map, add tile layer, and display
m = Map(center=tile_server.center())
m.add_layer(t)
m
```

![ipyleaflet](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/ipyleaflet.png)

#### 🥓 Two Rasters at Once

```py
from tileserver import get_leaflet_tile_layer
from ipyleaflet import Map, ScaleControl, FullScreenControl, SplitMapControl

m = Map(center=(37.7249511580583, -122.27230466902257), zoom=9)

# Create 2 tile layers from 2 separate raster files
l = get_leaflet_tile_layer('~/Desktop/TC_NG_SFBay_US_Geo.tif',
                           band=1, palette='matplotlib.Viridis_20', vmin=50, vmax=200)
r = get_leaflet_tile_layer('~/Desktop/small.tif',
                           band=2, palette='matplotlib.Plasma_6', vmin=0, vmax=150)

control = SplitMapControl(left_layer=l, right_layer=r)
m.add_control(control)
m.add_control(ScaleControl(position='bottomleft'))
m.add_control(FullScreenControl())
m
```

![ipyleaflet-double](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/ipyleaflet.gif)


Note: the color palette choices come from [`palettable`](https://jiffyclub.github.io/palettable/)


#### 🎯 Using `ipyleaflet` for ROI Extraction


```py
from tileserver import get_leaflet_tile_layer, TileServer
from ipyleaflet import Map, ScaleControl, FullScreenControl, DrawControl

# First, create a tile server from local raster file
tile_server = TileServer('~/Desktop/TC_NG_SFBay_US_Geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_server)

# Create ipyleaflet map, add layers, add draw control, display
m = Map(center=(37.7249511580583, -122.27230466902257), zoom=9)
m.add_layer(t)
m.add_control(ScaleControl(position='bottomleft'))
m.add_control(FullScreenControl())
draw_control = DrawControl()
m.add_control(draw_control)
m
```

![ipyleaflet-draw-roi](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/ipyleaflet-draw-roi.png)



```py
from shapely.geometry import Polygon

# Inspect `draw_control.data` to get the ROI
bbox = draw_control.data[0]
p = Polygon([tuple(l) for l in bbox['geometry']['coordinates'][0]])
left, bottom, right, top = p.bounds

roi_path = tile_server.extract_roi(left, right, bottom, top)
roi_path
```

```py
r = get_leaflet_tile_layer(roi_path)

m2 = Map(
        center=(37.7249511580583, -122.27230466902257),
        zoom=9,
       )
m2.add_layer(r)
m2.add_control(ScaleControl(position='bottomleft'))
m2.add_control(FullScreenControl())
m2
```

![ipyleaflet-roi](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/ipyleaflet-roi.png)


#### 🗺️ Example Datasets

A few example datasets are included with `tileserver`. A particularly
useful one has global elevation data which you can use to create high resolution Digital Elevation Models (DEMs) of a local region.

```py
from tileserver import get_leaflet_tile_layer, examples
from ipyleaflet import Map, DrawControl

# Load example tile layer from publicly available DEM source
tile_server = examples.get_elevation()

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_server,
                           band=1, vmin=-500, vmax=5000,
                           palette='mycarta.Cube1_19',
                           opacity=0.75)

m = Map(zoom=2)
m.add_layer(t)
draw_control = DrawControl()
m.add_control(draw_control)
m
```

![elevation](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/elevation.png)


Then you can follow the same routine as described above to extract an ROI.

I zoomed in over Golden, Colorado and drew a polygon of the extent of the DEM I would like to create:

![golden](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/golden-roi.png)

And perform the extraction:

```py
from shapely.geometry import Polygon

# Inspect `draw_control.data` to get the ROI
bbox = draw_control.data[0]
p = Polygon([tuple(l) for l in bbox['geometry']['coordinates'][0]])
left, bottom, right, top = p.bounds

roi_path = tile_server.extract_roi(left, right, bottom, top)

r = get_leaflet_tile_layer(roi_path, band=1,
                           palette='mycarta.Cube1_19', opacity=0.75)

m2 = Map(
        center=(39.763427033262175, -105.20614908076823),
        zoom=12,
       )
m2.add_layer(r)
m2
```

![golden-dem](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/golden-dem.png)

Here is another example with the Virtual Earth satellite imagery

```py
from tileserver import get_leaflet_tile_layer, examples
from ipyleaflet import Map, DrawControl

# Load example tile layer from publicly available imagery
tile_server = examples.get_virtual_earth()

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer(tile_server,opacity=1)

m = Map(center=(39.751343612695145, -105.22181306125279), zoom=18)
m.add_layer(t)
draw_control = DrawControl()
m.add_control(draw_control)
m
```

![kafadar](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/kafadar.png)


### 🖥️ Local Web Application

Launch the tileserver from the commandline to use the included web application where you can view the raster and extract regions of interest.

```bash
python -m tileserver path/to/raster.tif
```

![webviewer](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/webviewer.gif)

![webviewer-roi](https://raw.githubusercontent.com/banesullivan/flask-tileserver/main/imgs/webviewer-roi.gif)
