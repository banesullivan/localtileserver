# Local Tile Server

[![PyPI](https://img.shields.io/pypi/v/flask-tileserver.svg?logo=python&logoColor=white)](https://pypi.org/project/flask-tileserver/)

This is a simple Flask application for serving raster image tiles locally in the OGC standard.

This uses `large_image` and GeoJS for the web viewer included with the application. You can use the web viewer to select and extract regions of interest from rasters.

This also provides an interface for viewing local rasters with `ipyleaflet`.

## Installation

Install from PyPI: https://pypi.org/project/flask-tileserver/

```
pip install flask-tileserver
```

### Note on installing GDAL

GDAL can be a pain to install, and you may want to handle GDAL before install `flask-tileserver`.


If on linux, I highly recommend using the large_image_wheels from Kitware.

```
pip install --find-links=https://girder.github.io/large_image_wheels GDAL
```

Otherwise, I recommend using `conda`:

```
conda install -c conda-forge GDAL
```

## Usage

### Local Web Application

Launch the tileserver from the commandline to use the included web application where you can view the raster and extract regions of interest.

```bash
python -m tileserver path/to/raster.tif
```

![webviewer](./imgs/webviewer.gif)

![webviewer-roi](./imgs/webviewer-roi.gif)

### `ipyleaflet` Tile Layers

There are utilities included here for launching a tile server as a background thread to serve image tiles from any raster file on your
local file system. Further, I have inlcuded a utility for
automatically launching a tile server and creating an
`ipyleaflet.TileLayer`. Here is an example:

```py
from tileserver import get_leaflet_tile_layer
from ipyleaflet import Map, projections, ScaleControl, FullScreenControl, SplitMapControl

m = Map(
        center=(37.7249511580583, -122.27230466902257),
        zoom=9, crs=projections.EPSG3857,
       )

# Create two tile layers from 2 seperate raster files
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

![ipyleaflet](./imgs/ipyleaflet.gif)


Note: the color palette choices come form [`palettable`](https://jiffyclub.github.io/palettable/)


#### Using `ipyleaflet` for ROI Extraction


```py
from tileserver import get_leaflet_tile_layer, get_leaflet_tile_layer_from_tile_server, TileServer
from ipyleaflet import Map, projections, ScaleControl, FullScreenControl, DrawControl

# First, create a tile server from local raster file
tile_server = TileServer('~/Desktop/TC_NG_SFBay_US_Geo.tif')

# Create ipyleaflet tile layer from that server
t = get_leaflet_tile_layer_from_tile_server(tile_server)

# Create ipyleaflet, add layers, add draw control, display
m = Map(
        center=(37.7249511580583, -122.27230466902257),
        zoom=9, crs=projections.EPSG3857,
       )
m.add_layer(t)
m.add_control(ScaleControl(position='bottomleft'))
m.add_control(FullScreenControl())
draw_control = DrawControl()
m.add_control(draw_control)
m
```

![ipyleaflet-draw-roi](./imgs/ipyleaflet-draw-roi.png)



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
        zoom=9, crs=projections.EPSG3857,
       )
m2.add_layer(r)
m2.add_control(ScaleControl(position='bottomleft'))
m2.add_control(FullScreenControl())
m2
```

![ipyleaflet-roi](./imgs/ipyleaflet-roi.png)
