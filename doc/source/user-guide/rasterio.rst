🧩 Rasterio
-----------

``localtileserver.TileClient`` supports viewing ``rasterio.DatasetReader``
so that you can easily visualize your data when working with rasterio.
This will only work when opening a raster in read-mode.


.. jupyter-execute::

  import rasterio
  from ipyleaflet import Map
  from localtileserver import TileClient, get_leaflet_tile_layer

  src = rasterio.open('https://github.com/giswqs/data/raw/main/raster/srtm90.tif')

  client = TileClient(src)

  t = get_leaflet_tile_layer(client)

  m = Map(center=client.center(), zoom=client.default_zoom)
  m.add(t)
  m


``localtileserver`` actually uses ``rasterio`` under the hood for everything
and keeps a reference to a ``rasterio.DatasetReader`` for all clients.


.. jupyter-execute::

  from localtileserver import examples

  # Load example tile layer from publicly available DEM source
  client = examples.get_elevation()

  client.dataset
