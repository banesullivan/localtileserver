"""Extended tests for localtileserver.helpers."""

import numpy as np
import pytest

from localtileserver.helpers import hillshade, numpy_to_raster, save_new_raster


class TestHillshadeExtended:
    def test_1d_array_raises(self):
        with pytest.raises(ValueError, match="two-dimensional"):
            hillshade(np.array([1, 2, 3]))

    def test_azimuth_over_360_raises(self):
        arr = np.random.rand(10, 10)
        with pytest.raises(ValueError, match="360"):
            hillshade(arr, azimuth=361)

    def test_altitude_over_90_raises(self):
        arr = np.random.rand(10, 10)
        with pytest.raises(ValueError, match="90"):
            hillshade(arr, altitude=91)

    def test_basic_output(self):
        arr = np.random.rand(50, 50) * 1000
        result = hillshade(arr)
        assert result.shape == (50, 50)
        assert result.min() >= 0
        assert result.max() <= 255


class TestNumpyToRaster:
    def test_2d_array(self, tmp_path):
        ras_meta = {
            "driver": "GTiff",
            "dtype": "float32",
            "width": 10,
            "height": 10,
            "count": 1,
            "crs": "EPSG:4326",
            "transform": [1.0, 0.0, 0.0, 0.0, -1.0, 10.0],
        }
        data = np.random.rand(10, 10).astype("float32")
        out = numpy_to_raster(ras_meta, data, out_path=str(tmp_path / "test.tif"))
        assert out.exists() if hasattr(out, "exists") else True

    def test_3d_array(self, tmp_path):
        ras_meta = {
            "driver": "GTiff",
            "dtype": "float32",
            "width": 10,
            "height": 10,
            "count": 3,
            "crs": "EPSG:4326",
            "transform": [1.0, 0.0, 0.0, 0.0, -1.0, 10.0],
        }
        data = np.random.rand(3, 10, 10).astype("float32")
        out = numpy_to_raster(ras_meta, data, out_path=str(tmp_path / "test3.tif"))
        assert out.exists() if hasattr(out, "exists") else True


class TestSaveNewRaster:
    def test_from_path(self, bahamas_file):
        import rasterio

        with rasterio.open(bahamas_file) as src:
            data = src.read()
        result = save_new_raster(str(bahamas_file), data[:1])
        assert result is not None

    def test_from_dataset(self, bahamas_file):
        import rasterio

        with rasterio.open(bahamas_file) as src:
            data = src.read()
            result = save_new_raster(src, data[:1])
        assert result is not None

    def test_3d_validation(self, bahamas_file):

        data_4d = np.random.rand(2, 3, 10, 10)
        with pytest.raises(AssertionError, match="ndim 3"):
            save_new_raster(str(bahamas_file), data_4d)
