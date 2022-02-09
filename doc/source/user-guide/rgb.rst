🧮 Controlling the RGB Bands
----------------------------

The ``ipyleaflet`` and ``folium`` tile layer utilities support setting which bands
to view as the RGB channels. To set the RGB bands, pass a length three list
of the band indices to the ``band`` argument.

Here is an example where I create two tile layers from the same raster but
viewing a different set of bands:

.. code:: python

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


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet-multi-bands.png
