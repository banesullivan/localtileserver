🌐 localtileserver
==================

.. toctree::
   :hidden:

   installation/index
   user-guide/index
   api/index



*Need to visualize a rather large (gigabytes+) raster?* **This is for you.**

  Try it out below!

.. jupyter-execute::

  from localtileserver import TileClient, get_leaflet_tile_layer, examples
  from ipyleaflet import Map

  # Create a TileClient from a raster file
  # client = TileClient('path/to/geo.tif')
  client = examples.get_san_francisco()  # use example data

  # Create ipyleaflet TileLayer from that server
  t = get_leaflet_tile_layer(client)
  # Create ipyleaflet map, add tile layer, and display
  m = Map(center=client.center(), zoom=client.default_zoom)
  m.add(t)
  m



.. raw:: html

  <br/>


A Python package for serving tiles from large raster files in
the `Slippy Maps standard <https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames>`_
(i.e., `/zoom/x/y.png`) for visualization in Jupyter with ``ipyleaflet`` or ``folium``.


.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/banesullivan/localtileserver-demo/HEAD
   :alt: MyBinder

Launch a `demo <https://github.com/banesullivan/localtileserver-demo>`_ on MyBinder |binder|


Built on `rio-tiler <https://github.com/cogeotiff/rio-tiler>`_ and
`FastAPI <https://fastapi.tiangolo.com/>`_.


🌟 Highlights
=============

- Launch a tile server for large geospatial images
- View local or remote raster files with ``ipyleaflet`` or ``folium`` in Jupyter
- **Band math expressions** for on-the-fly computed imagery (e.g., NDVI)
- **Per-band statistics** and **multiple image stretch modes**
- **Multiple output formats**: PNG, JPEG, WebP, GeoTIFF, NPY
- **Spatial subsetting** via bounding box crops and GeoJSON masks
- `STAC <https://stacspec.org/>`_ item support for multi-asset catalogs
- `Xarray <https://xarray.dev/>`_ DataArray tile serving (NetCDF, Zarr, etc.)
- **Virtual mosaics** from multiple raster files
- View rasters with CesiumJS with the built-in web application
- Full REST API powered by FastAPI with auto-generated OpenAPI docs

ℹ️ Overview
===========

The :class:`TileClient` class can be used to launch a tile server in a background
thread which will serve raster imagery to a viewer (see ``ipyleaflet`` and
``folium`` examples in :ref:`user_guide`).

This tile server can efficiently deliver varying resolutions of your
raster imagery to your viewer; it helps to have pre-tiled,
`Cloud Optimized GeoTIFFs (COG) <https://www.cogeo.org/>`_.

The server exposes a comprehensive REST API built on
`FastAPI <https://fastapi.tiangolo.com/>`_, including support for
band math expressions, per-band statistics, multiple image stretch modes,
spatial subsetting, STAC catalogs, xarray DataArrays, and virtual mosaics.
Interactive API docs are available at ``/swagger/``.

There is an included, standalone web viewer leveraging
`CesiumJS <https://cesium.com/platform/cesiumjs/>`_.


🪢 Community Usage
==================

- `leafmap <https://github.com/giswqs/leafmap>`_ and `geemap <https://github.com/giswqs/geemap>`_: use localtileserver for visualizing large raster images in a Jupyter-based geospatial mapping application
- `streamlit-geospatial <https://github.com/giswqs/streamlit-geospatial>`_: uses localtileserver's remote tile server for viewing image tiles
- `remotetileserver <https://github.com/banesullivan/remotetileserver>`_: uses the core FastAPI application to spin up a production ready tile server
- `Kaustav Mukherjee's blog post <https://kaustavmukherjee-66179.medium.com/visualize-raster-tiles-locally-using-localtileserver-0-4-1-and-jupyter-notebook-cccd59e6420a>`_: a user-created demonstration on how to get started with localtileserver
- `Serving up SpaceNet Imagery for Bokeh <https://medium.com/geodesic/serving-up-spacenet-imagery-for-bokeh-e85b8fffe05>`_: Adam Van Etten's blog post using localtileserver to view imagery with Bokeh
