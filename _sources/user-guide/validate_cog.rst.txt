✅ Validate COG
---------------

``localtileserver`` includes a helper method to validate whether or not a
source image meets the requirements of a Cloud Optimized GeoTiff.

:func:`localtileserver.validate.validate_cog` users the
``validate_cloud_optimized_geotiff`` script from ``osgeo_utils`` to check if
an image is a GeoTiff with the proper tiling and overviews to be considered
"Cloud Optimized". If the validation fails, this method will raise an
:class:`localtileserver.validate.ValidateCloudOptimizedGeoTIFFException`
error.

You can use the script by:

.. jupyter-execute::

   from localtileserver.validate import validate_cog

   # Path to raster (URL or local path)
   url = 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'

   # If invalid, raises ValidateCloudOptimizedGeoTIFFException
   validate_cog(url)


This can also be used with an existing :class:`localtileserver.TileClient`:

.. jupyter-execute::

   from localtileserver import examples
   from localtileserver.validate import validate_cog

   tile_client = examples.get_san_francisco()

   # If invalid, raises ValidateCloudOptimizedGeoTIFFException
   validate_cog(tile_client)
