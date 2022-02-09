🌐 localtileserver
==================

.. toctree::
   :hidden:

   installation/index
   user-guide/index
   api/index



*Need to visualize a rather large (gigabytes) raster you have locally?* **This is for you.**


.. raw:: html

  <br>

  <div id="map" style="width: 100%; height: 400px;"></div>

  <script>
    var map = L.map('map').setView([37.752, -122.418], 9);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}.png', {
        attribution: 'Map tiles by <a href="https://carto.com">Carto</a>, under CC BY 3.0. Data by <a href="https://www.openstreetmap.org/">OpenStreetMap</a>, under ODbL.'
    }).addTo(map);

    L.tileLayer('https://tileserver.banesullivan.com/api/tiles/{z}/{x}/{y}.png?projection=EPSG:3857&filename=https://data.kitware.com/api/v1/file/60747d792fa25629b9a79565/download', {
        attribution: 'Raster file served by <a href="https://github.com/banesullivan/localtileserver" target="_blank">localtileserver</a>.',
        subdomains: '',
        crossOrigin: false,
    }).addTo(map);


  </script>

  <br>



.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/banesullivan/localtileserver-demo/HEAD
   :alt: MyBinder


A Flask application for serving tiles from large raster files in
the `Slippy Maps standard <https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames>`_
(i.e., ``/zoom/x/y.png``)

Launch a `demo <https://github.com/banesullivan/localtileserver-demo>`_ on MyBinder |binder|


🌟 Highlights
-------------

- Launch a tile server for large geospatial images
- View local or remote* raster files with `ipyleaflet` or `folium` in Jupyter
- View rasters with CesiumJS with the built-in Flask web application
- Extract regions of interest (ROIs) interactively
- Use the example datasets to generate Digital Elevation Models

*remote raster files should be pre-tiled Cloud Optimized GeoTiffs*

ℹ️ Overview
-----------

This is a Flask application (blueprint) for serving tiles of large images.
The `TileClient` class can be used to to launch a tile server in a background
thread which will serve raster imagery to a viewer (see `ipyleaflet` and
`folium` Jupyter notebook examples below).

This tile server can efficiently deliver varying levels of detail of your
raster imagery to your viewer; it helps to have pre-tiled, Cloud Optimized
GeoTIFFs (COG), but no wories if not as the backing libraries,
`large_image <https://github.com/girder/large_image>`_,
will tile and cache for you when opening the raster.

There is an included, standalone web viewer leveraging
`CesiumJS <https://cesium.com/platform/cesiumjs/>`_ and `GeoJS <https://opengeoscience.github.io/geojs/>`_.
You can use the web viewer to select and extract regions of interest from rasters.


.. note::

   This is a hobby project and I am doing my best to make it
   more stable/robust. Things might break between minor releases (I use the
   ``major.minor.patch`` versioning scheme).


🪢 Community Usage
------------------

- `leafmap <https://github.com/giswqs/leafmap>`_ and `geemap <https://github.com/giswqs/geemap>`_: use localtileserver for visualizing large raster images in a Jupyter-based geospatial mapping application
- `streamlit-geospatial <https://github.com/giswqs/streamlit-geospatial>`_: uses localtileserver's flask-based remote tile server for viewing image tiles
- `remotetileserver <https://github.com/banesullivan/remotetileserver>`_: uses the core flask application to spin up a production ready tile server
- `Kaustav Mukherjee's blog post <https://kaustavmukherjee-66179.medium.com/visualize-raster-tiles-locally-using-localtileserver-0-4-1-and-jupyter-notebook-cccd59e6420a>`_: a user-created demonstration on how to get started with localtileserver
