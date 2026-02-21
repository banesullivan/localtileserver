🗺️ Spatial Subsets
-------------------

``localtileserver`` supports extracting spatial subsets from raster files via
bounding box crops (parts) and GeoJSON feature masks. These are useful for
downloading specific regions of interest from large rasters.


Bounding Box Crops (Part Reads)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extract a rectangular region from a raster by specifying a bounding box:

.. code:: bash

    # Bounding box as left,bottom,right,top
    GET /api/part.png?filename=geo.tif&bbox=-78.0,25.0,-77.0,26.0

The ``bbox`` parameter takes four comma-separated float values representing
the bounding box in ``left,bottom,right,top`` order.

Additional parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``bbox``
     - Bounding box as ``left,bottom,right,top`` (required)
   * - ``bounds_crs``
     - CRS of the bounding box coordinates (default: dataset's native CRS)
   * - ``dst_crs``
     - Target CRS for the output image
   * - ``max_size``
     - Maximum output dimension in pixels (default: 1024)
   * - ``indexes``
     - Band indexes to read (comma-separated)
   * - ``expression``
     - Band math expression to compute
   * - ``colormap``
     - Colormap to apply
   * - ``vmin``, ``vmax``
     - Value range for rescaling
   * - ``stretch``
     - Stretch mode to apply

Example with CRS specification:

.. code:: bash

    # Crop in geographic coordinates
    GET /api/part.png?filename=geo.tif&bbox=-78.0,25.0,-77.0,26.0&bounds_crs=EPSG:4326

    # Download as GeoTIFF for GIS analysis
    GET /api/part.tif?filename=geo.tif&bbox=-78.0,25.0,-77.0,26.0&bounds_crs=EPSG:4326


GeoJSON Feature Masks
^^^^^^^^^^^^^^^^^^^^^

Extract data masked to a GeoJSON polygon or geometry. This uses a ``POST``
request with the GeoJSON as the request body:

.. code:: bash

    # POST a GeoJSON Feature or Geometry
    POST /api/feature.png?filename=geo.tif
    Content-Type: application/json

    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-77.5, 25.5],
          [-77.0, 25.5],
          [-77.0, 26.0],
          [-77.5, 26.0],
          [-77.5, 25.5]
        ]]
      },
      "properties": {}
    }

You can also pass a bare GeoJSON Geometry (without the ``Feature`` wrapper) --
it will be automatically wrapped.

Additional parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``dst_crs``
     - Target CRS for the output image
   * - ``max_size``
     - Maximum output dimension in pixels (default: 1024)
   * - ``indexes``
     - Band indexes to read
   * - ``expression``
     - Band math expression
   * - ``colormap``
     - Colormap to apply
   * - ``vmin``, ``vmax``
     - Value range for rescaling
   * - ``stretch``
     - Stretch mode to apply

All output formats (PNG, JPEG, WebP, GeoTIFF, NPY) are supported for both
part and feature endpoints.
