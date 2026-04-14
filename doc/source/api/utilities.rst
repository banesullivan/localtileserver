Utilities
=========


Colormap & Palettes
-------------------

.. autofunction:: localtileserver.tiler.palettes.get_palettes

.. autofunction:: localtileserver.tiler.palettes.register_colormap

.. autofunction:: localtileserver.tiler.palettes.get_registered_colormap

.. autofunction:: localtileserver.tiler.palettes.palette_valid_or_raise


Helpers
-------

.. autoclass:: localtileserver.tiler.utilities.ImageBytes
   :members:
   :undoc-members:

.. autofunction:: localtileserver.helpers.hillshade

.. autofunction:: localtileserver.helpers.save_new_raster

.. autofunction:: localtileserver.helpers.parse_shapely

.. autofunction:: localtileserver.helpers.polygon_to_geojson

.. autofunction:: localtileserver.helpers.numpy_to_raster

.. autofunction:: localtileserver.validate.validate_cog

.. autofunction:: localtileserver.tiler.utilities.make_vsi

.. autofunction:: localtileserver.tiler.utilities.format_to_encoding

.. autofunction:: localtileserver.tiler.utilities.get_clean_filename

.. autofunction:: localtileserver.tiler.utilities.get_cache_dir

.. autofunction:: localtileserver.tiler.utilities.purge_cache


Configuration
-------------

.. autofunction:: localtileserver.configure.get_default_client_params

.. autoclass:: localtileserver.manager.AppManager
   :members:
   :undoc-members:


Application Factory
-------------------

.. autofunction:: localtileserver.web.fastapi_app.create_app

.. autofunction:: localtileserver.web.fastapi_app.run_app


Diagnostics
-----------

.. autoclass:: localtileserver.Report
   :members:
   :undoc-members:
