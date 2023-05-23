import os

import numpy as np
from osgeo import gdal
import pytest

from localtileserver import helpers
from localtileserver.tileserver import get_data_path

skip_rasterio = False
try:
    import rasterio as rio
except ImportError:
    skip_rasterio = True


def test_hillshade():
    path = str(get_data_path("co_elevation_roi.tif"))
    ds = gdal.Open(path)
    dem = ds.ReadAsArray()
    hs_arr = helpers.hillshade(dem)
    assert isinstance(hs_arr, np.ndarray)


@pytest.mark.skipif(skip_rasterio, reason="rasterio not installed")
def test_save_new_raster():
    path = get_data_path("co_elevation_roi.tif")
    src = rio.open(path)
    path = helpers.save_new_raster(src, np.random.rand(10, 10))
    assert os.path.exists(path)
