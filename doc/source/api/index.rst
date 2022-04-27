📖 API
======


Python Client
-------------

.. autofunction:: localtileserver.get_or_create_tile_client


.. autoclass:: localtileserver.client.BaseTileClient
   :members:
   :undoc-members:


.. autoclass:: localtileserver.TileClient
   :members:
   :undoc-members:


.. autoclass:: localtileserver.RemoteTileClient
   :members:
   :undoc-members:


Jupyter Widget Helpers
----------------------

.. autofunction:: localtileserver.get_leaflet_tile_layer


.. autofunction:: localtileserver.get_leaflet_roi_controls


.. autofunction:: localtileserver.get_folium_tile_layer



Other Helpers
-------------

.. autofunction:: localtileserver.helpers.save_new_raster

.. autofunction:: localtileserver.make_vsi

.. autofunction:: localtileserver.validate.validate_cog


Exceptions
----------


.. autoclass:: localtileserver.validate.ValidateCloudOptimizedGeoTIFFException
   :members:
   :undoc-members:
