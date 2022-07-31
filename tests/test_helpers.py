import os

import numpy as np
from osgeo import gdal
import pytest

from localtileserver import helpers
from localtileserver.tileserver import get_co_elevation_url
from localtileserver.tileserver.utilities import make_vsi

skip_rasterio = False
try:
    import rasterio as rio
except ImportError:
    skip_rasterio = True


def test_hillshade():
    ds = gdal.Open(make_vsi(get_co_elevation_url()))
    dem = ds.ReadAsArray()
    hs_arr = helpers.hillshade(dem)
    assert isinstance(hs_arr, np.ndarray)


@pytest.mark.skipif(skip_rasterio, reason="rasterio not installed")
def test_save_new_raster():
    src = rio.open(make_vsi(get_co_elevation_url()))
    path = helpers.save_new_raster(src, np.random.rand(10, 10))
    assert os.path.exists(path)
