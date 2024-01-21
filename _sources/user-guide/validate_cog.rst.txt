✅ Validate COG
---------------

``localtileserver`` includes a helper method to validate whether or not a
source image meets the requirements of a Cloud Optimized GeoTiff.

:func:`localtileserver.validate.validate_cog` uses rio-cogeo to validate
whether or not a source image meets the requirements of a Cloud Optimized
GeoTIFF.

You can use the script by:

.. jupyter-execute::

   from localtileserver import validate_cog

   # Path to raster (URL or local path)
   url = 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'

   # If invalid, returns False
   validate_cog(url)


This can also be used with an existing :class:`localtileserver.TileClient`:

.. jupyter-execute::

   from localtileserver import examples, validate_cog

   client = examples.get_san_francisco()

   # If invalid, returns False
   validate_cog(client)
