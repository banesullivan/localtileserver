📦 Xarray DataArray Support
---------------------------

``localtileserver`` can serve tiles directly from
`xarray <https://xarray.dev/>`_ DataArrays, enabling visualization of
NetCDF, Zarr, HDF5, and other multi-dimensional datasets without converting
them to GeoTIFF first.

This feature uses `rio-tiler's XarrayReader <https://cogeotiff.github.io/rio-tiler/readers/#xarray>`_
and requires the ``xarray`` optional dependency group.


Installation
^^^^^^^^^^^^

Install with xarray support:

.. code:: bash

    pip install localtileserver[xarray]

Or install the dependencies directly:

.. code:: bash

    pip install xarray rioxarray


Creating a DataArray for Tile Serving
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Your DataArray must have:

1. Spatial dimensions (``x``/``y`` or ``lon``/``lat``)
2. A CRS set via ``rioxarray``

.. code:: python

    import xarray as xr
    import numpy as np

    # Open a NetCDF dataset
    ds = xr.open_dataset('temperature.nc')
    da = ds['temperature']

    # Ensure CRS is set (required)
    da = da.rio.write_crs('EPSG:4326')
    da = da.rio.set_spatial_dims(x_dim='lon', y_dim='lat')

For Zarr datasets:

.. code:: python

    ds = xr.open_dataset(
        'https://example.com/data.zarr',
        engine='zarr',
        decode_coords='all',
    )
    da = ds['variable_name']
    da = da.rio.write_crs('EPSG:4326')


Python Handler Functions
^^^^^^^^^^^^^^^^^^^^^^^^

Use the handler functions directly for programmatic access:

.. code:: python

    from localtileserver.tiler.xarray_handler import (
        get_xarray_reader,
        get_xarray_info,
        get_xarray_statistics,
        get_xarray_tile,
        get_xarray_preview,
    )

    # Create a reader
    reader = get_xarray_reader(da)

    # Get metadata
    info = get_xarray_info(reader)
    print(f"Bounds: {info['bounds']}")
    print(f"CRS: {info['crs']}")
    print(f"Shape: {info['width']}x{info['height']}")

    # Get statistics
    stats = get_xarray_statistics(reader)
    for band, s in stats.items():
        print(f"{band}: min={s['min']}, max={s['max']}")

    # Get a preview thumbnail
    thumb = get_xarray_preview(reader, max_size=256)

    # Get a tile (you need to know valid tile coordinates)
    from morecantile import tms
    bounds = reader.bounds
    tiles = list(tms.get('WebMercatorQuad').tiles(*bounds, zooms=8))
    t = tiles[0]
    tile = get_xarray_tile(reader, t.z, t.x, t.y)


REST API Endpoints
^^^^^^^^^^^^^^^^^^

Xarray DataArrays are registered in the server's in-memory registry
(since they cannot be serialized as URLs). The REST endpoints are
prefixed with ``/api/xarray/``:

.. code:: bash

    # Get info (key identifies the registered dataset)
    GET /api/xarray/info?key=temperature

    # Get statistics
    GET /api/xarray/statistics?key=temperature

    # Get a tile
    GET /api/xarray/tiles/{z}/{x}/{y}.png?key=temperature

    # Get a thumbnail
    GET /api/xarray/thumbnail.png?key=temperature&max_size=512

If only one dataset is registered, the ``key`` parameter can be omitted.


Registering a DataArray with the Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use the REST API, register your DataArray with the application:

.. code:: python

    from localtileserver.web import create_app
    from localtileserver.tiler.xarray_handler import get_xarray_reader

    app = create_app()
    reader = get_xarray_reader(da)
    app.state.xarray_registry = {'temperature': reader}


Supported Data Types
^^^^^^^^^^^^^^^^^^^^

The xarray support works with any data that ``rioxarray`` can handle:

- **NetCDF** (``.nc``) -- via ``xr.open_dataset()``
- **Zarr** (``.zarr``) -- via ``xr.open_dataset(engine='zarr')``
- **HDF5** (``.h5``, ``.hdf5``) -- via ``xr.open_dataset(engine='h5netcdf')``
- **GRIB** (``.grib``, ``.grib2``) -- via ``xr.open_dataset(engine='cfgrib')``
- **In-memory** arrays -- construct a ``DataArray`` from NumPy arrays with coordinates

.. note::

    The DataArray must be 2D (single band) or 3D (multi-band with the band
    dimension as the first axis). 4D+ arrays are not supported directly --
    select a time step or level first using xarray's ``.sel()`` or ``.isel()``.
