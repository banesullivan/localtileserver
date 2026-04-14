Handler Functions
=================

Core tile generation, statistics, and image manipulation functions for
raster files, STAC catalogs, xarray DataArrays, and virtual mosaics.


Tile Handlers
-------------

.. autofunction:: localtileserver.tiler.handler.get_reader

.. autofunction:: localtileserver.tiler.handler.get_tile

.. autofunction:: localtileserver.tiler.handler.get_preview

.. autofunction:: localtileserver.tiler.handler.get_statistics

.. autofunction:: localtileserver.tiler.handler.get_meta_data

.. autofunction:: localtileserver.tiler.handler.get_source_bounds

.. autofunction:: localtileserver.tiler.handler.get_point

.. autofunction:: localtileserver.tiler.handler.get_part

.. autofunction:: localtileserver.tiler.handler.get_feature


STAC Handlers
-------------

Functions for working with STAC (SpatioTemporal Asset Catalog) items.

.. autofunction:: localtileserver.tiler.stac.get_stac_reader

.. autofunction:: localtileserver.tiler.stac.get_stac_info

.. autofunction:: localtileserver.tiler.stac.get_stac_statistics

.. autofunction:: localtileserver.tiler.stac.get_stac_tile

.. autofunction:: localtileserver.tiler.stac.get_stac_preview


Xarray Handlers
---------------

Functions for serving tiles from xarray DataArrays. Requires the ``xarray``
optional dependency group (``pip install localtileserver[xarray]``).

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_reader

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_info

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_statistics

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_tile

.. autofunction:: localtileserver.tiler.xarray_handler.get_xarray_preview


Mosaic Handlers
---------------

Functions for creating virtual mosaics from multiple raster files.

.. autofunction:: localtileserver.tiler.mosaic.get_mosaic_tile

.. autofunction:: localtileserver.tiler.mosaic.get_mosaic_preview
