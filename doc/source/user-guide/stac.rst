🛰️ STAC Support
-----------------

``localtileserver`` provides built-in support for
`STAC (SpatioTemporal Asset Catalog) <https://stacspec.org/>`_ items,
enabling you to visualize and serve tiles from multi-asset STAC catalogs
without downloading data locally.

This feature uses `rio-tiler's STACReader <https://cogeotiff.github.io/rio-tiler/readers/#stac>`_
under the hood.


REST API Endpoints
^^^^^^^^^^^^^^^^^^

All STAC endpoints are prefixed with ``/api/stac/`` and require a ``url``
query parameter pointing to a STAC Item JSON document.

**Get STAC item info:**

.. code:: bash

    GET /api/stac/info?url=https://example.com/stac/item.json

    # Filter to specific assets
    GET /api/stac/info?url=https://example.com/stac/item.json&assets=B04,B03,B02

**Get statistics:**

.. code:: bash

    GET /api/stac/statistics?url=https://example.com/stac/item.json&assets=B04

**Get tiles:**

.. code:: bash

    # Tile from specific assets
    GET /api/stac/tiles/{z}/{x}/{y}.png?url=https://example.com/stac/item.json&assets=visual

    # Tile with band math expression across assets
    GET /api/stac/tiles/{z}/{x}/{y}.png?url=https://example.com/stac/item.json&expression=(B04_b1-B03_b1)/(B04_b1+B03_b1)

**Get thumbnail:**

.. code:: bash

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
     - Comma-separated list of asset names to use (e.g., ``visual``,
       ``B04,B03,B02``)
   * - ``expression``
     - Band math expression for cross-asset computations
   * - ``max_size``
     - Maximum thumbnail dimension (default: 512)

Example with ``requests``:

.. code:: python

    import requests
    from IPython.display import Image, display

    stac_url = "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2A_T10SEG_20230101T190201_L2A"

    # Get item info
    resp = requests.get('http://localhost:8000/api/stac/info',
                        params={'url': stac_url})
    info = resp.json()
    print("Available assets:", list(info.keys()))

    # Get a thumbnail from the visual asset
    resp = requests.get('http://localhost:8000/api/stac/thumbnail.png',
                        params={'url': stac_url, 'assets': 'visual'})
    display(Image(data=resp.content))


Python Handler Functions
^^^^^^^^^^^^^^^^^^^^^^^^

For programmatic use without the REST API, you can use the handler functions
directly:

.. code:: python

    from localtileserver.tiler.stac import (
        get_stac_reader,
        get_stac_info,
        get_stac_statistics,
        get_stac_tile,
        get_stac_preview,
    )

    # Create a reader from a STAC item URL
    reader = get_stac_reader('https://example.com/stac/item.json')

    # Get available assets and metadata
    info = get_stac_info(reader, assets=['visual'])

    # Get per-asset/band statistics
    stats = get_stac_statistics(reader, assets=['B04'])

    # Get a tile
    tile = get_stac_tile(reader, z=10, x=512, y=512, assets=['visual'])

    # Get a thumbnail
    thumb = get_stac_preview(reader, assets=['visual'], max_size=256)
