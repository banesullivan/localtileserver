📖 API
======


Python Client
-------------

.. autofunction:: localtileserver.get_or_create_tile_client


.. autoclass:: localtileserver.client.TilerInterface
   :members:
   :undoc-members:


.. autoclass:: localtileserver.TileClient
   :members:
   :undoc-members:


Jupyter Widget Helpers
----------------------

.. autofunction:: localtileserver.get_leaflet_tile_layer


.. autofunction:: localtileserver.get_folium_tile_layer


Tile Handler Functions
----------------------

Core tile generation, statistics, and image manipulation functions.

.. autofunction:: localtileserver.tiler.handler.get_tile

.. autofunction:: localtileserver.tiler.handler.get_preview

.. autofunction:: localtileserver.tiler.handler.get_statistics

.. autofunction:: localtileserver.tiler.handler.get_part

.. autofunction:: localtileserver.tiler.handler.get_feature

.. autofunction:: localtileserver.tiler.handler.get_reader

.. autofunction:: localtileserver.tiler.handler.get_meta_data

.. autofunction:: localtileserver.tiler.handler.get_source_bounds

.. autofunction:: localtileserver.tiler.handler.get_point


STAC Handler Functions
----------------------

Functions for working with STAC (SpatioTemporal Asset Catalog) items.

.. autofunction:: localtileserver.tiler.stac.get_stac_reader

.. autofunction:: localtileserver.tiler.stac.get_stac_info

.. autofunction:: localtileserver.tiler.stac.get_stac_statistics

.. autofunction:: localtileserver.tiler.stac.get_stac_tile

.. autofunction:: localtileserver.tiler.stac.get_stac_preview


Xarray Handler Functions
-------------------------

Functions for serving tiles from xarray DataArrays. Requires the ``xarray``
optional dependency group (``pip install localtileserver[xarray]``).

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_reader

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_info

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_statistics

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_tile

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_preview


Mosaic Handler Functions
------------------------

Functions for creating virtual mosaics from multiple raster files.

.. autofunction:: localtileserver.tiler.mosaic.get_mosaic_tile

.. autofunction:: localtileserver.tiler.mosaic.get_mosaic_preview


Colormap & Palette Functions
----------------------------

.. autofunction:: localtileserver.tiler.palettes.get_palettes

.. autofunction:: localtileserver.tiler.palettes.register_colormap

.. autofunction:: localtileserver.tiler.palettes.get_registered_colormap


Utility Functions
-----------------

.. autofunction:: localtileserver.tiler.utilities.format_to_encoding

.. autofunction:: localtileserver.tiler.utilities.get_clean_filename

.. autofunction:: localtileserver.tiler.utilities.make_vsi

.. autofunction:: localtileserver.helpers.save_new_raster

.. autofunction:: localtileserver.validate.validate_cog

.. autofunction:: localtileserver.helpers.polygon_to_geojson


Application Factory
-------------------

.. autofunction:: localtileserver.web.fastapi_app.create_app

.. autofunction:: localtileserver.web.fastapi_app.run_app
