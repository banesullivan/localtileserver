🧮 Band Math Expressions
------------------------

``localtileserver`` supports on-the-fly band math expressions, enabling you to
compute derived imagery like vegetation indices (NDVI), normalized difference
water indices (NDWI), and custom band combinations without pre-processing your
raster data.

Expressions use the syntax from `rio-tiler <https://cogeotiff.github.io/rio-tiler/>`_
where bands are referenced as ``b1``, ``b2``, ``b3``, etc. (1-indexed).


Basic Usage
^^^^^^^^^^^

Use the ``expression`` parameter with :func:`get_leaflet_tile_layer` or the
``TileClient`` methods:

.. code:: python

    from localtileserver import TileClient, get_leaflet_tile_layer
    from ipyleaflet import Map

    client = TileClient('path/to/multispectral.tif')

    # NDVI: (NIR - Red) / (NIR + Red)
    # Assuming band 4 = NIR, band 1 = Red
    t = get_leaflet_tile_layer(client,
                               expression='(b4-b1)/(b4+b1)',
                               vmin=-1, vmax=1,
                               colormap='RdYlGn')

    m = Map(center=client.center(), zoom=client.default_zoom)
    m.add(t)
    m


Common Expressions
^^^^^^^^^^^^^^^^^^

Here are some frequently used band math expressions for Landsat-style imagery:

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Index
     - Expression
     - Description
   * - NDVI
     - ``(b4-b3)/(b4+b3)``
     - Normalized Difference Vegetation Index
   * - NDWI
     - ``(b3-b4)/(b3+b4)``
     - Normalized Difference Water Index
   * - EVI
     - ``2.5*(b4-b3)/(b4+6*b3-7.5*b1+1)``
     - Enhanced Vegetation Index
   * - Simple Ratio
     - ``b4/b3``
     - NIR/Red ratio
   * - Brightness
     - ``(b1+b2+b3)/3``
     - Average visible brightness

.. note::

    Band numbering is 1-indexed and corresponds to the band order in the source
    raster file. Check your file's metadata to identify which bands correspond
    to which wavelengths.


REST API
^^^^^^^^

Expressions can also be used via the REST API:

.. code:: bash

    # Tile with NDVI expression
    GET /api/tiles/{z}/{x}/{y}.png?filename=multispectral.tif&expression=(b4-b1)/(b4+b1)&vmin=-1&vmax=1&colormap=RdYlGn

    # Thumbnail with expression
    GET /api/thumbnail.png?filename=multispectral.tif&expression=(b4-b1)/(b4+b1)


.. note::

    When using ``expression``, the ``indexes`` parameter is ignored. They are
    mutually exclusive: use one or the other.
