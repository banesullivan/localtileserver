🩻 Non-geospatial visualization
-------------------------------

We can visualize any image (geospatial or otherwise) with ipyleaflet by
specifying a ``crs`` of ``ipyleaflet.projections.Simple`` and telling
``localtileserver`` to use a projection of ``None`` when serving the tiles.

This will work to visualize any image (e.g., medical microscopy images).

.. jupyter-execute::

  from ipyleaflet import Map, projections
  from localtileserver import TileClient, examples, get_leaflet_tile_layer

  client = examples.get_landsat(default_projection=None)

  # Image layer that fetches tiles in image coordinates
  image_layer = get_leaflet_tile_layer(client)

  # Make the ipyleaflet map
  m = Map(crs=projections.Simple,  # no projection
          basemap=image_layer,  # basemap is the source image
          min_zoom=0, max_zoom=client.max_zoom, zoom=0,  # handle zoom defaults
         )
  m


Or with folium:

.. jupyter-execute::

  from folium import Map
  from localtileserver import TileClient, examples, get_folium_tile_layer

  client = examples.get_landsat(default_projection=None)

  # Image layer that fetches tiles in image coordinates
  image_layer = get_folium_tile_layer(client)

  # Make the folium map
  m = Map(crs='Simple',  # no projection
          tiles=None,  # no basemap
          min_zoom=0, max_zoom=client.max_zoom, start_zoom=0,  # handle zoom defaults
         )
  m.add_child(image_layer)
  m
