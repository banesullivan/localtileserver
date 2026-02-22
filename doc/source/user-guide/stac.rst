🛰️ STAC Support
-----------------

``localtileserver`` provides built-in support for
`STAC (SpatioTemporal Asset Catalog) <https://stacspec.org/>`_ items,
enabling you to visualize and serve tiles from multi-asset STAC catalogs
without downloading data locally.

This feature uses `rio-tiler's STACReader <https://cogeotiff.github.io/rio-tiler/readers/#stac>`_
under the hood.


Python API
^^^^^^^^^^

The ``STACClient`` class provides the same workflow as ``TileClient`` but for
remote STAC items:

.. jupyter-execute::

  from localtileserver import STACClient
  from IPython.display import Image, display

  stac_url = (
      "https://earth-search.aws.element84.com/v1/"
      "collections/sentinel-2-l2a/items/S2A_T10SEG_20230101T190201_L2A"
  )

  client = STACClient(stac_url, assets=["visual"])

  # Geographic extent
  print("Bounds:", client.bounds())
  print("Center:", client.center())

.. jupyter-execute::

  # Available assets
  info = client.stac_info()
  print("Assets:", list(info.keys()))

.. jupyter-execute::

  # Thumbnail preview
  display(Image(data=client.thumbnail(max_size=256)))

``STACClient`` also works with ``get_leaflet_tile_layer`` for interactive
maps in Jupyter:

.. code:: python

    from localtileserver import get_leaflet_tile_layer
    from ipyleaflet import Map, ScaleControl, FullScreenControl

    layer = get_leaflet_tile_layer(client)
    m = Map(center=client.center(), zoom=client.default_zoom)
    m.add(layer)
    m.add_control(ScaleControl(position='bottomleft'))
    m.add_control(FullScreenControl())
    m


REST API
^^^^^^^^

All STAC endpoints are also available via the REST API, prefixed with
``/api/stac/``:

.. code:: bash

    # Get STAC item info
    GET /api/stac/info?url=https://example.com/stac/item.json

    # Get statistics
    GET /api/stac/statistics?url=https://example.com/stac/item.json&assets=B04

    # Get a tile
    GET /api/stac/tiles/{z}/{x}/{y}.png?url=https://example.com/stac/item.json&assets=visual

    # Get a thumbnail
    GET /api/stac/thumbnail.png?url=https://example.com/stac/item.json&assets=visual&max_size=512


Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``url``
     - URL to a STAC Item JSON document (required)
   * - ``assets``
     - Asset names to use (e.g., ``["visual"]`` or ``["B04", "B03", "B02"]``)
   * - ``expression``
     - Band math expression for cross-asset computations
   * - ``max_size``
     - Maximum thumbnail dimension (default: 512)
