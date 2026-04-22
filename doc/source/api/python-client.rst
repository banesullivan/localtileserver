Python Client
=============

Core classes and helpers for launching a tile server and integrating with
Jupyter mapping libraries.


TileClient
----------

.. autoclass:: localtileserver.TileClient
   :members:
   :undoc-members:
   :show-inheritance:

.. autofunction:: localtileserver.open

.. autofunction:: localtileserver.get_or_create_tile_client

.. autoclass:: localtileserver.client.TilerInterface
   :members:
   :undoc-members:

.. autoclass:: localtileserver.client.TileServerMixin
   :members:
   :undoc-members:


STACClient
----------

A client for serving tiles directly from a
`STAC <https://stacspec.org/>`_ item URL, without requiring a local file.

.. autoclass:: localtileserver.STACClient
   :members:
   :undoc-members:
   :show-inheritance:


Jupyter Widget Helpers
----------------------

.. autofunction:: localtileserver.get_leaflet_tile_layer

.. autofunction:: localtileserver.get_folium_tile_layer

.. autoclass:: localtileserver.LocalTileServerLayerMixin
