📖 API Reference
================

.. toctree::
   :hidden:

   python-client
   examples
   handlers
   utilities
   rest-api


:doc:`python-client`
    Core :class:`~localtileserver.TileClient`, mixin classes, and Jupyter widget helpers
    (:func:`~localtileserver.get_leaflet_tile_layer`, :func:`~localtileserver.get_folium_tile_layer`).

:doc:`examples`
    Factory functions that return a pre-loaded :class:`~localtileserver.TileClient`
    for quick experimentation with publicly available sample data.

:doc:`handlers`
    Low-level tile generation, statistics, and image manipulation functions for
    raster files, STAC catalogs, xarray DataArrays, and virtual mosaics.

:doc:`utilities`
    Colormap and palette registration, raster helpers, configuration,
    application factory, and diagnostics.

:doc:`rest-api`
    Complete HTTP endpoint reference for the FastAPI-powered REST API,
    including STAC, xarray, and mosaic endpoints.
