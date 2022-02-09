🥓 Two Rasters at Once
----------------------

.. code:: python

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


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet.gif
