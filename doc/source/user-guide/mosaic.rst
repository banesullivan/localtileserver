🧩 Virtual Mosaics
-------------------

``localtileserver`` supports creating virtual mosaics from multiple raster
files, compositing them into a single seamless tile layer. This uses
`rio-tiler's mosaic_reader <https://cogeotiff.github.io/rio-tiler/mosaic/>`_
and does not require the ``cogeo-mosaic`` package.


How It Works
^^^^^^^^^^^^

The mosaic handler takes a list of raster file paths (or URLs) and serves
tiles by reading from each file and compositing the results using a pixel
selection method. The default method is "first valid pixel wins" -- meaning
the first file in the list that has valid data at a given pixel location
provides the value.


Python Handler Functions
^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from localtileserver.tiler.mosaic import get_mosaic_tile, get_mosaic_preview

    # List of raster files to mosaic
    files = [
        'path/to/scene_north.tif',
        'path/to/scene_south.tif',
    ]

    # Get a mosaic thumbnail
    thumb = get_mosaic_preview(files, max_size=512)

    # Get a mosaic tile at a specific location
    tile = get_mosaic_tile(files, z=10, x=512, y=512)

You can specify band indexes:

.. code:: python

    # Single band mosaic with colormap
    tile = get_mosaic_tile(files, z=10, x=512, y=512, indexes=[1])


Pixel Selection Methods
^^^^^^^^^^^^^^^^^^^^^^^

By default, the mosaic uses ``FirstMethod`` (first valid pixel wins). You
can use any of rio-tiler's built-in pixel selection methods:

.. code:: python

    from rio_tiler.mosaic.methods.defaults import (
        FirstMethod,
        HighestMethod,
        LowestMethod,
        MeanMethod,
        MedianMethod,
    )

    # Use the highest pixel value from overlapping areas
    tile = get_mosaic_tile(files, z=10, x=512, y=512,
                           pixel_selection=HighestMethod)

    # Use the mean of overlapping pixels
    tile = get_mosaic_tile(files, z=10, x=512, y=512,
                           pixel_selection=MeanMethod)


REST API Endpoints
^^^^^^^^^^^^^^^^^^

Mosaic endpoints are prefixed with ``/api/mosaic/``:

.. code:: bash

    # Get a mosaic tile (files via query parameter)
    GET /api/mosaic/tiles/{z}/{x}/{y}.png?files=scene_north.tif,scene_south.tif

    # Get a mosaic thumbnail
    GET /api/mosaic/thumbnail.png?files=scene_north.tif,scene_south.tif&max_size=512

    # With band selection
    GET /api/mosaic/tiles/{z}/{x}/{y}.png?files=scene_north.tif,scene_south.tif&indexes=1,2,3

Parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``files``
     - Comma-separated list of file paths or URLs (or register
       ``mosaic_assets`` in app state)
   * - ``indexes``
     - Comma-separated band indexes
   * - ``max_size``
     - Maximum thumbnail dimension (default: 512)


Server-Side Registration
^^^^^^^^^^^^^^^^^^^^^^^^

For files that are cumbersome to pass as query parameters, you can register
them in the application state:

.. code:: python

    from localtileserver.web import create_app

    app = create_app()
    app.state.mosaic_assets = [
        'path/to/scene_north.tif',
        'path/to/scene_south.tif',
    ]

Then access the mosaic endpoints without the ``files`` parameter:

.. code:: bash

    GET /api/mosaic/tiles/{z}/{x}/{y}.png
    GET /api/mosaic/thumbnail.png
