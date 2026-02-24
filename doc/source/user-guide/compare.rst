🥓 Two Rasters at Once
----------------------

.. jupyter-execute::

  from localtileserver import TileClient, get_leaflet_tile_layer
  from localtileserver.tiler.data import get_landsat_vegas_b30_url, get_landsat_vegas_b70_url
  from ipyleaflet import Map, ScaleControl, FullScreenControl, SplitMapControl

  # Create tile servers from two raster files
  l_client = TileClient(get_landsat_vegas_b30_url())
  r_client = TileClient(get_landsat_vegas_b70_url())

  # Shared display parameters
  display = dict(vmin=50, vmax=150, colormap='coolwarm')

  # Create 2 tile layers from different raster
  l = get_leaflet_tile_layer(l_client, **display)
  r = get_leaflet_tile_layer(r_client, **display)

  # Make the ipyleaflet map
  m = Map(center=l_client.center(), zoom=l_client.default_zoom)
  control = SplitMapControl(left_layer=l, right_layer=r)
  m.add_control(control)
  m.add_control(ScaleControl(position='bottomleft'))
  m.add_control(FullScreenControl())
  m
