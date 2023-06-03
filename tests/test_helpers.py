import os

import numpy as np
import rasterio

from localtileserver import helpers
from localtileserver.tiler import get_data_path


def test_hillshade():
    path = str(get_data_path("co_elevation_roi.tif"))
    ds = rasterio.open(path)
    dem = ds.read(1)
    hs_arr = helpers.hillshade(dem)
    assert isinstance(hs_arr, np.ndarray)


def test_save_new_raster():
    path = get_data_path("co_elevation_roi.tif")
    src = rasterio.open(path)
    path = helpers.save_new_raster(src, np.random.rand(10, 10))
    assert os.path.exists(path)
