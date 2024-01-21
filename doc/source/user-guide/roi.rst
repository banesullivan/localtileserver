🎯 ROI Extraction
-----------------

The :class:`localtileserver.TileClient` class has a few methods for extracting
regions of interest (ROIs):

- :func:`localtileserver.TileClient.extract_roi`
- :func:`localtileserver.TileClient.extract_roi_shape`

These methods can be used to extract rectangular regions from large images
using world coordinates, Shapely geometry, or pixel bounds.

.. note::

  The following example needs ``shapely`` to be installed.


.. jupyter-execute::

  from localtileserver import examples, get_leaflet_tile_layer
  from ipyleaflet import Map, WKTLayer

  client = examples.get_san_francisco()
  presidio_roi = examples.load_presidio()

  presidio_layer = WKTLayer(
    wkt_string=presidio_roi.wkt,
    style={'fillOpacity': 0, 'weight': 1},
    hover_style={
        'color': 'white', 'fillOpacity': 0
    },
  )

  m = Map(center=client.center(), zoom=client.default_zoom)
  m.add_layer(get_leaflet_tile_layer(client))
  m.add_layer(presidio_layer)
  m

Perform ROI extraction with Shapely object

.. jupyter-execute::

  presidio = client.extract_roi_shape(presidio_roi, encoding='PNG', return_bytes=True)
  presidio


-------


.. code:: python

    from localtileserver import TileClient, get_leaflet_tile_layer, examples
    from ipyleaflet import Map, WKTLayer

    client = examples.get_san_francisco()
    presidio_roi = examples.load_presidio()

    # Perform ROI extraction with Shapely object
    presidio = client.extract_roi_shape(presidio_roi)

    presidio_layer = WKTLayer(
      wkt_string=presidio.wkt,
      style={'fillOpacity': 0, 'weight': 1},
      hover_style={
          'color': 'white', 'fillOpacity': 0
      },
    )

    m = Map(center=presidio.center(), zoom=presidio.default_zoom)
    m.add_layer(get_leaflet_tile_layer(presidio))
    m.add_layer(presidio_layer)
    m


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/presidio.png


User Interface with ``ipyleaflet``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I have included the :func:`get_leaflet_roi_controls` utility to create some leaflet
UI controls for extracting regions of interest from a tile client. You can
use it as follows and then draw a polygon and click the "Extract ROI" button.

The outputs are save in your working directory by default (next to the Jupyter notebook).

.. code:: python

  from localtileserver import get_leaflet_tile_layer, get_leaflet_roi_controls
  from localtileserver import examples
  from ipyleaflet import Map

  # First, create a TileClient from example raster file
  client = examples.get_san_francisco()

  # Create ipyleaflet tile layer from that server
  t = get_leaflet_tile_layer(client)

  # Create ipyleaflet controls to extract an ROI
  draw_control, roi_control = get_leaflet_roi_controls(client)

  # Create ipyleaflet map, add layers, add controls, and display
  m = Map(center=(37.7249511580583, -122.27230466902257), zoom=9)
  m.add_layer(t)
  m.add_control(draw_control)
  m.add_control(roi_control)
  m


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet-draw-roi.png
