🗺️ Example Datasets
-------------------

A few example datasets are included with `localtileserver`. A particularly
useful one has global elevation data which you can use to create high resolution Digital Elevation Models (DEMs) of a local region.


.. code:: python

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


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/elevation.png


Then you can follow the same routine as described above to extract an ROI.

I zoomed in over Golden, Colorado and drew a polygon of the extent of the DEM I would like to create:

.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/golden-roi.png

And perform the extraction:

.. code:: python

  roi_path = '...'  # Look in your working directory

  r = get_leaflet_tile_layer(roi_path, band=1,
                             palette='plasma', opacity=0.75)

  m2 = Map(
          center=(39.763427033262175, -105.20614908076823),
          zoom=12,
         )
  m2.add_layer(r)
  m2


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/golden-dem.png

Here is another example with the Virtual Earth satellite imagery

.. code:: python

  from localtileserver import get_leaflet_tile_layer, examples
  from ipyleaflet import Map

  # Load example tile layer from publicly available imagery
  tile_client = examples.get_virtual_earth()

  # Create ipyleaflet tile layer from that server
  t = get_leaflet_tile_layer(tile_client, opacity=1)

  m = Map(center=(39.751343612695145, -105.22181306125279), zoom=18)
  m.add_layer(t)
  m


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/kafadar.png
