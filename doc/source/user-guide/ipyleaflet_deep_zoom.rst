🔬 Deep Zoom with ``ipyleaflet``
--------------------------------

In order to perform deep zooming of tile sources with ``ipyleaflet``, you must
specify a few keyword arguments:

- ``max_zoom`` and ``max_native_zoom`` set appropriately in the ``TileLayer``
- ``max_zoom`` set in the ``Map`` which matches ``max_zoom`` in the ``TileLayer``

.. jupyter-execute::

  from localtileserver import get_leaflet_tile_layer, examples
  from ipyleaflet import Map, TileLayer

  # Load high res raster
  tile_client = examples.get_oam2()

  max_zoom = 30

  # Create zoomable tile layer from high res raster
  layer = get_leaflet_tile_layer(tile_client,
      # extra kwargs to pass to the TileLayer
      max_zoom=max_zoom,
      max_native_zoom=max_zoom,
  )

  # Make the ipyleaflet map with deeper zoom
  m = Map(center=tile_client.center(),
          zoom=22, max_zoom=max_zoom
  )
  m.add_layer(layer)
  m
