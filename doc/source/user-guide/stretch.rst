🔧 Image Stretch Modes
----------------------

``localtileserver`` supports several image stretch modes to enhance the visual
contrast of your raster data. Stretch modes control how raw pixel values are
mapped to the 0-255 display range.


Available Stretch Modes
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Mode
     - Description
   * - ``none``
     - No stretch; assumes data is already in 0-255 range.
   * - ``minmax``
     - Linear stretch from the absolute minimum to the absolute maximum of
       the dataset.
   * - ``linear``
     - Percentile stretch from the 2nd to the 98th percentile. This is the
       most commonly used stretch for removing outliers while preserving
       contrast.
   * - ``equalize``
     - Histogram equalization. Redistributes pixel values to produce a
       uniform histogram, maximizing contrast.
   * - ``sqrt``
     - Square root stretch. Applies a square-root transformation after
       min/max normalization. Useful for data with a right-skewed distribution.
   * - ``log``
     - Logarithmic stretch. Applies a log transformation after min/max
       normalization. Useful for data with a very large dynamic range.


REST API
^^^^^^^^

The ``stretch`` parameter is available on all tile and thumbnail endpoints:

.. code:: bash

    # Tile with linear stretch
    GET /api/tiles/{z}/{x}/{y}.png?filename=dem.tif&stretch=linear

    # Thumbnail with histogram equalization
    GET /api/thumbnail.png?filename=dem.tif&stretch=equalize

    # Thumbnail with square root stretch
    GET /api/thumbnail.png?filename=dem.tif&stretch=sqrt


.. note::

    Stretch modes are currently available via the REST API tile and thumbnail
    endpoints. When a ``stretch`` mode is specified, it overrides any
    ``vmin``/``vmax`` values that would otherwise be used.
