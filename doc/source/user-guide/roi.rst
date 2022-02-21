🎯 Using ``ipyleaflet`` for ROI Extraction
------------------------------------------

I have included the :func:`get_leaflet_roi_controls` utility to create some leaflet
UI controls for extracting regions of interest from a tile client. You can
use it as follows and then draw a polygon and click the "Extract ROI" button.

The outputs are save in your working directory by default (next to the Jupyter notebook).

.. code:: python

  from localtileserver import get_leaflet_tile_layer, get_leaflet_roi_controls
  from localtileserver import examples
  from ipyleaflet import Map

  # First, create a TileClient from example raster file
  tile_client = examples.get_san_francisco()

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


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet-draw-roi.png
