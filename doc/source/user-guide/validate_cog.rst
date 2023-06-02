✅ Validate COG
---------------

``localtileserver`` includes a helper method to validate whether or not a
source image meets the requirements of a Cloud Optimized GeoTiff.

:func:`localtileserver.validate.validate_cog` users the
``validate_cloud_optimized_geotiff`` script from ``osgeo_utils`` to check if
an image is a GeoTiff with the proper tiling and overviews to be considered
"Cloud Optimized". If the validation fails, this method will raise an
``osgeo_utils.samples.validate_cloud_optimized_geotiff.ValidateCloudOptimizedGeoTIFFException``
error.

You can use the script by:

.. jupyter-execute::

   from localtileserver import validate_cog

   # Path to raster (URL or local path)
   url = 'https://data.kitware.com/api/v1/file/626854a14acac99f42126a74/download'

   # If invalid, raises ValidateCloudOptimizedGeoTIFFException
   validate_cog(url)


This can also be used with an existing :class:`localtileserver.TileClient`:

.. jupyter-execute::

   from localtileserver import examples, validate_cog

   client = examples.get_san_francisco()

   # If invalid, raises ValidateCloudOptimizedGeoTIFFException
   validate_cog(client)


↔️ Converting to a COG
~~~~~~~~~~~~~~~~~~~~~~

Converting an image to a Cloud Optimized GeoTiff, while easy, isn't always
straightforward. I often find myself needing to recall *exactly* how to do it
or need to point people to a resource on how to perform the conversion *so that
the resulting image is not only a COG but a performant COG.*

This *brief* section is a place for me to note how to convert imagery to a
COG.

The easiest method is to use ``large_image_converter``: https://pypi.org/project/large-image-converter/

.. code-block:: python

  import large_image_converter

  large_image_converter.convert(str(input_path), str(output_path))

Under the hood, this is using GDAL's translate utility to perform the
conversion with a few cleverly chosen options set to better (opinionated)
default values:

.. code-block:: bash

  gdal_translate <input> <output>.tiff \
    -of COG \
    -co BIGTIFF=IF_SAFER \
    -co BLOCKSIZE=256 \
    -co COMPRESS=LZW \
    -co PREDICTOR=YES \
    -co QUALITY=90

or in Python:

.. code-block:: python

  from osgeo import gdal

  options = [
         '-of',
         'COG',
         '-co',
         'BIGTIFF=IF_SAFER',
         '-co',
         'COMPRESS=LZW',
         '-co',
         'PREDICTOR=YES',
         '-co',
         'BLOCKSIZE=256',
         '-co',
         'QUALITY=90'
     ]

  ds = gdal.Open(src_path)
  ds = gdal.Translate(output_path, ds, options=options)


I want to elaborate a bit on what I meant when I stated the statement above:

  so that the resulting image is not only a COG but a performant COG.

I'm planning to write a thorough blog post on this topic, but the gist is that
a COG is a performant COG when two criteria are properly met:

1. **Tiling:** the bytes of the image data are arranged in tiles such that data that are geographically close are adjacent within the file. This is opposed to typical striping patterns.
2. **Overviews:** Embedded in the image are “zoomed out”, lower-resolution versions of the image down to 256x256 pixels (or 512x512), effectively creating a pyramid of resolutions.

`cogeo.org <https://www.cogeo.org/in-depth.html>`_ does a wonderful job
explaining these concepts - for further details, please refer to their in-depth
explanation.

While many routines to generate a COG exist out there, many of them do not
properly handle both tiling and generating overviews. Often, this is not a big
deal, but when dealing with massive amounts of imagery, the tiling block
sizes, compression scheme, and ensuring overviews are present can make
significant performances increases.
