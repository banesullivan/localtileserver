REST API Reference
==================

``localtileserver`` exposes a comprehensive REST API built on
`FastAPI <https://fastapi.tiangolo.com/>`_. Interactive API documentation
is available at ``/swagger/`` when the server is running.


Core Tile Endpoints
-------------------

These endpoints serve tiles and metadata for raster files specified via the
``filename`` query parameter. If no ``filename`` is provided the server falls
back to the file configured at startup (via ``app.state.filename``) or the
built-in San Francisco Bay example data.

.. list-table::
   :header-rows: 1
   :widths: 35 10 55

   * - Endpoint
     - Method
     - Description
   * - ``/api/tiles/{z}/{x}/{y}.{fmt}``
     - GET
     - Serve a single map tile at the given zoom/x/y coordinates.
   * - ``/api/thumbnail.{fmt}``
     - GET
     - Serve a thumbnail preview of the entire raster.
   * - ``/api/metadata``
     - GET
     - Return raster metadata (CRS, bounds, band info, dtype, etc.).
   * - ``/api/bounds``
     - GET
     - Return geographic bounds in a specified CRS.
   * - ``/api/statistics``
     - GET
     - Return per-band statistics (min, max, mean, std, histogram).
   * - ``/api/validate``
     - GET
     - Validate whether the file is a Cloud Optimized GeoTIFF.
   * - ``/api/palettes``
     - GET
     - List all available color palettes.
   * - ``/api/part.{fmt}``
     - GET
     - Extract a bounding box crop from the raster.
   * - ``/api/feature.{fmt}``
     - POST
     - Extract data masked to a GeoJSON feature (POST body).


Common Query Parameters
-----------------------

Most tile, thumbnail, and statistics endpoints accept these parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``filename``
     - Path or URL to the raster file.
   * - ``indexes``
     - Comma-separated band indexes (e.g., ``1,2,3``).
   * - ``colormap``
     - Colormap name (e.g., ``terrain``, ``viridis``), or a JSON color
       definition.
   * - ``vmin``
     - Minimum value for rescaling (comma-separated for per-band values).
   * - ``vmax``
     - Maximum value for rescaling (comma-separated for per-band values).
   * - ``nodata``
     - Override the file's nodata value.
   * - ``expression``
     - Band math expression (e.g., ``(b4-b1)/(b4+b1)``). Mutually exclusive
       with ``indexes``.
   * - ``stretch``
     - Stretch mode: ``none``, ``minmax``, ``linear``, ``equalize``, ``sqrt``,
       ``log``.


Endpoint-Specific Parameters
-----------------------------

``/api/bounds``
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``crs``
     - Output coordinate reference system (default: ``EPSG:4326``).


``/api/thumbnail.{fmt}``
^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``max_size``
     - Maximum pixel dimension of the thumbnail (default: ``512``).
   * - ``crs``
     - Reproject the thumbnail to this CRS before returning.


``/api/part.{fmt}``
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``bbox``
     - **Required.** Bounding box as ``left,bottom,right,top``
       (comma-separated floats).
   * - ``max_size``
     - Maximum pixel dimension of the output image (default: ``1024``).
   * - ``bounds_crs``
     - CRS of the ``bbox`` coordinates (default: ``EPSG:4326``).
   * - ``dst_crs``
     - CRS to reproject the output image into.


``/api/feature.{fmt}``
^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``max_size``
     - Maximum pixel dimension of the output image (default: ``1024``).
   * - ``dst_crs``
     - CRS to reproject the output image into.

The POST body must be a GeoJSON feature object used to clip the raster.


Output Formats
--------------

The ``{fmt}`` path parameter controls the output format:

- ``png`` -- PNG (default)
- ``jpeg`` / ``jpg`` -- JPEG
- ``webp`` -- WebP
- ``tif`` / ``tiff`` / ``geotiff`` -- GeoTIFF
- ``npy`` -- NumPy array


STAC Endpoints
--------------

Endpoints for visualizing `STAC <https://stacspec.org/>`_ catalog items.

.. list-table::
   :header-rows: 1
   :widths: 40 10 50

   * - Endpoint
     - Method
     - Description
   * - ``/api/stac/info``
     - GET
     - Get STAC item metadata and available assets.
   * - ``/api/stac/statistics``
     - GET
     - Get per-asset/band statistics.
   * - ``/api/stac/tiles/{z}/{x}/{y}.{fmt}``
     - GET
     - Serve tiles from a STAC item's assets.
   * - ``/api/stac/thumbnail.{fmt}``
     - GET
     - Serve a thumbnail from a STAC item.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``url``
     - **Required.** URL pointing to the STAC Item JSON.
   * - ``assets``
     - Comma-separated asset names to include (e.g., ``B04,B03,B02``).
   * - ``expression``
     - Band math expression over asset names (e.g., ``(B04-B03)/(B04+B03)``).
       Applies to tiles and thumbnails.
   * - ``max_size``
     - Maximum pixel dimension of the thumbnail (default: ``512``).
       Applies to ``/api/stac/thumbnail.{fmt}`` only.


Xarray Endpoints
----------------

Endpoints for serving tiles from in-memory xarray DataArrays. DataArrays must
be pre-registered in the server's ``xarray_registry`` before use.

.. list-table::
   :header-rows: 1
   :widths: 40 10 50

   * - Endpoint
     - Method
     - Description
   * - ``/api/xarray/info``
     - GET
     - Get DataArray metadata.
   * - ``/api/xarray/statistics``
     - GET
     - Get per-band statistics.
   * - ``/api/xarray/tiles/{z}/{x}/{y}.{fmt}``
     - GET
     - Serve tiles from a registered DataArray.
   * - ``/api/xarray/thumbnail.{fmt}``
     - GET
     - Serve a thumbnail from a registered DataArray.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``key``
     - Registry key identifying the DataArray. If only one DataArray is
       registered the key may be omitted.
   * - ``indexes``
     - Comma-separated band indexes to include.
   * - ``max_size``
     - Maximum pixel dimension of the thumbnail (default: ``512``).
       Applies to ``/api/xarray/thumbnail.{fmt}`` only.


Mosaic Endpoints
----------------

Endpoints for creating virtual mosaics composited from multiple raster files.

.. list-table::
   :header-rows: 1
   :widths: 40 10 50

   * - Endpoint
     - Method
     - Description
   * - ``/api/mosaic/tiles/{z}/{x}/{y}.{fmt}``
     - GET
     - Serve mosaic tiles composited from multiple raster files.
   * - ``/api/mosaic/thumbnail.{fmt}``
     - GET
     - Serve a mosaic thumbnail.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``files``
     - Comma-separated file paths or URLs to mosaic. If omitted the server
       falls back to ``app.state.mosaic_assets``.
   * - ``indexes``
     - Comma-separated band indexes to include.
   * - ``max_size``
     - Maximum pixel dimension of the thumbnail (default: ``512``).
       Applies to ``/api/mosaic/thumbnail.{fmt}`` only.


Interactive Documentation
-------------------------

When the server is running, visit ``/swagger/`` for the full interactive
OpenAPI documentation. This is auto-generated by FastAPI and allows you to
try out all endpoints directly in your browser.
