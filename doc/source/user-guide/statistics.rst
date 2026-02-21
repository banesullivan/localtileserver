📊 Statistics API
-----------------

``localtileserver`` provides a per-band statistics endpoint that returns
comprehensive information about the data distribution in your raster file.
This is useful for understanding data ranges, choosing appropriate ``vmin``/``vmax``
values, and quality-checking your data.


Python Client
^^^^^^^^^^^^^

Use the ``statistics()`` method on a ``TileClient`` instance:

.. code:: python

    from localtileserver import TileClient

    client = TileClient('path/to/geo.tif')

    # Get statistics for all bands
    stats = client.statistics()

    for band_name, band_stats in stats.items():
        print(f"{band_name}:")
        print(f"  min={band_stats['min']}, max={band_stats['max']}")
        print(f"  mean={band_stats['mean']}, std={band_stats['std']}")
        print(f"  percentile_2={band_stats['percentile_2']}")
        print(f"  percentile_98={band_stats['percentile_98']}")


Statistics with Expressions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also compute statistics on derived bands using expressions:

.. code:: python

    # Statistics for NDVI
    stats = client.statistics(expression='(b4-b1)/(b4+b1)')


REST API
^^^^^^^^

Statistics are available via the REST endpoint:

.. code:: bash

    # Per-band statistics
    GET /api/statistics?filename=geo.tif

    # Statistics for specific bands
    GET /api/statistics?filename=geo.tif&indexes=1,2

    # Statistics for an expression
    GET /api/statistics?filename=geo.tif&expression=(b4-b1)/(b4+b1)


Response Format
^^^^^^^^^^^^^^^

The statistics response is a JSON dictionary keyed by band name (e.g., ``b1``,
``b2``). Each band contains:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``min``
     - Minimum pixel value
   * - ``max``
     - Maximum pixel value
   * - ``mean``
     - Mean pixel value
   * - ``std``
     - Standard deviation
   * - ``median``
     - Median pixel value
   * - ``count``
     - Total number of pixels (including masked)
   * - ``valid_pixels``
     - Number of valid (unmasked) pixels
   * - ``masked_pixels``
     - Number of masked pixels
   * - ``valid_percent``
     - Percentage of valid pixels
   * - ``percentile_2``
     - 2nd percentile value
   * - ``percentile_98``
     - 98th percentile value
   * - ``histogram``
     - Histogram as ``[counts, bin_edges]``
   * - ``majority``
     - Most common pixel value
   * - ``minority``
     - Least common pixel value
   * - ``unique``
     - Number of unique pixel values
