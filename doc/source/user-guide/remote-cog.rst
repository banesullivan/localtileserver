☁️ Remote Cloud Optimized GeoTiffs (COGs)
-----------------------------------------

While ``localtileserver`` is intended to be used only with raster files existing
on your local filesystem, there is support for URL files through GDAL's
`Virtual Storage Interface <https://gdal.org/user/virtual_file_systems.html>`_.
Simply pass your ``http<s>://`` or ``s3://`` URL to the :class:`TileClient`. This will
work quite well for pre-tiled Cloud Optimized GeoTiffs, but I do not recommend
doing this with non-tiled raster formats.

For example, the raster at the url below is ~3GiB but because it is pre-tiled,
we can view tiles of the remote file very efficiently in a Jupyter notebook.

.. code:: python

  from localtileserver import get_folium_tile_layer
  from localtileserver import TileClient
  from folium import Map

  url = 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'

  # First, create a tile server from local raster file
  tile_client = TileClient(url)

  # Create folium tile layer from that server
  t = get_folium_tile_layer(tile_client)

  m = Map(location=tile_client.center())
  m.add_child(t)
  m

.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/vsi-raster.png

Note that the Virtual Storage Interface is a complex API, and :class:`TileClient`
currently only handles ``vsis3`` and ``vsicurl``. If you need a different VFS
mechanism, simply create your ``/vsi`` path and pass that to :class:`TileClient`.
