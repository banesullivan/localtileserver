"""Tests for Xarray/DataArray support (Phase 3.2)."""

import numpy as np
import pytest

xr = pytest.importorskip("xarray")
rioxarray = pytest.importorskip("rioxarray")

from rio_tiler.io.xarray import XarrayReader  # noqa: E402

from localtileserver.tiler.xarray_handler import (  # noqa: E402
    _check_xarray,
    get_xarray_info,
    get_xarray_preview,
    get_xarray_reader,
    get_xarray_statistics,
    get_xarray_tile,
)


@pytest.fixture
def sample_data_array():
    """Create a synthetic DataArray suitable for XarrayReader."""
    # 3-band, 64x64 pixels with geographic CRS covering a small area
    data = np.random.randint(0, 255, (3, 64, 64), dtype=np.uint8)
    y = np.linspace(25.0, 26.0, 64)
    x = np.linspace(-78.0, -77.0, 64)
    da = xr.DataArray(
        data,
        dims=["band", "y", "x"],
        coords={"band": [1, 2, 3], "y": y, "x": x},
        name="test_array",
    )
    da = da.rio.write_crs("EPSG:4326")
    da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
    return da


@pytest.fixture
def sample_reader(sample_data_array):
    """Create an XarrayReader from the sample DataArray."""
    return XarrayReader(sample_data_array)


@pytest.fixture
def single_band_data_array():
    """Create a 2D (single-band) DataArray."""
    data = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
    y = np.linspace(25.0, 26.0, 64)
    x = np.linspace(-78.0, -77.0, 64)
    da = xr.DataArray(
        data,
        dims=["y", "x"],
        coords={"y": y, "x": x},
        name="single_band",
    )
    da = da.rio.write_crs("EPSG:4326")
    da = da.rio.set_spatial_dims(x_dim="x", y_dim="y")
    return da


class TestCheckXarray:
    def test_no_error(self):
        # Should not raise when xarray is installed
        _check_xarray()


class TestGetXarrayReader:
    def test_creates_reader(self, sample_data_array):
        reader = get_xarray_reader(sample_data_array)
        assert isinstance(reader, XarrayReader)

    def test_reader_has_bounds(self, sample_data_array):
        reader = get_xarray_reader(sample_data_array)
        assert reader.bounds is not None
        assert len(reader.bounds) == 4

    def test_reader_has_crs(self, sample_data_array):
        reader = get_xarray_reader(sample_data_array)
        assert reader.crs is not None


class TestGetXarrayInfo:
    def test_info_returns_dict(self, sample_reader):
        info = get_xarray_info(sample_reader)
        assert isinstance(info, dict)
        assert "bounds" in info
        assert "crs" in info
        assert "dtype" in info


class TestGetXarrayStatistics:
    def test_statistics_returns_dict(self, sample_reader):
        stats = get_xarray_statistics(sample_reader)
        assert isinstance(stats, dict)
        assert len(stats) > 0
        # Each band should have min, max, mean, etc.
        for _key, val in stats.items():
            assert "min" in val
            assert "max" in val
            assert "mean" in val

    def test_statistics_with_indexes(self, sample_reader):
        stats = get_xarray_statistics(sample_reader, indexes=[1])
        assert len(stats) == 1


class TestGetXarrayTile:
    def test_tile_returns_image(self, sample_reader):
        # Find a valid tile for the data extent (around lat 25-26, lon -78 to -77)
        # At zoom 8, we can find a tile that covers this area
        from morecantile import tms

        bounds = sample_reader.bounds
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=8))
        assert len(tiles) > 0
        t = tiles[0]
        result = get_xarray_tile(sample_reader, t.z, t.x, t.y)
        assert result.mimetype == "image/png"
        assert len(bytes(result)) > 0

    def test_tile_jpeg_format(self, sample_reader):
        from morecantile import tms

        bounds = sample_reader.bounds
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=8))
        t = tiles[0]
        result = get_xarray_tile(sample_reader, t.z, t.x, t.y, img_format="JPEG")
        assert result.mimetype == "image/jpeg"

    def test_tile_with_indexes(self, sample_reader):
        from morecantile import tms

        bounds = sample_reader.bounds
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=8))
        t = tiles[0]
        result = get_xarray_tile(sample_reader, t.z, t.x, t.y, indexes=[1])
        assert result.mimetype == "image/png"


class TestGetXarrayPreview:
    def test_preview_returns_image(self, sample_reader):
        result = get_xarray_preview(sample_reader)
        assert result.mimetype == "image/png"
        assert len(bytes(result)) > 0

    def test_preview_with_max_size(self, sample_reader):
        result = get_xarray_preview(sample_reader, max_size=32)
        assert result.mimetype == "image/png"
        assert len(bytes(result)) > 0

    def test_preview_jpeg(self, sample_reader):
        result = get_xarray_preview(sample_reader, img_format="JPEG")
        assert result.mimetype == "image/jpeg"

    def test_preview_with_indexes(self, sample_reader):
        result = get_xarray_preview(sample_reader, indexes=[1, 2])
        assert result.mimetype == "image/png"


class TestSingleBand:
    def test_single_band_reader(self, single_band_data_array):
        reader = get_xarray_reader(single_band_data_array)
        assert reader is not None

    def test_single_band_info(self, single_band_data_array):
        reader = get_xarray_reader(single_band_data_array)
        info = get_xarray_info(reader)
        assert info["count"] == 1

    def test_single_band_preview(self, single_band_data_array):
        reader = get_xarray_reader(single_band_data_array)
        result = get_xarray_preview(reader)
        assert result.mimetype == "image/png"


class TestXarrayRouter:
    @pytest.fixture
    def xarray_client(self, sample_data_array):
        from fastapi.testclient import TestClient

        from localtileserver.web import create_app

        app = create_app()
        # Register a DataArray via the registry
        reader = XarrayReader(sample_data_array)
        if not hasattr(app.state, "xarray_registry"):
            app.state.xarray_registry = {}
        app.state.xarray_registry["test"] = reader
        with TestClient(app) as c:
            yield c

    def test_xarray_info_endpoint(self, xarray_client):
        resp = xarray_client.get("/api/xarray/info?key=test")
        assert resp.status_code == 200
        data = resp.json()
        assert "bounds" in data
        assert "crs" in data

    def test_xarray_statistics_endpoint(self, xarray_client):
        resp = xarray_client.get("/api/xarray/statistics?key=test")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0

    def test_xarray_thumbnail_endpoint(self, xarray_client):
        resp = xarray_client.get("/api/xarray/thumbnail.png?key=test")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_xarray_tile_endpoint(self, xarray_client, sample_data_array):
        from morecantile import tms

        reader = XarrayReader(sample_data_array)
        bounds = reader.bounds
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=8))
        t = tiles[0]
        resp = xarray_client.get(f"/api/xarray/tiles/{t.z}/{t.x}/{t.y}.png?key=test")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_xarray_no_registry(self):
        from fastapi.testclient import TestClient

        from localtileserver.web import create_app

        app = create_app()
        with TestClient(app) as c:
            resp = c.get("/api/xarray/info")
            assert resp.status_code == 400

    def test_xarray_key_not_found(self, xarray_client):
        resp = xarray_client.get("/api/xarray/info?key=nonexistent")
        assert resp.status_code == 404

    def test_xarray_bad_format(self, xarray_client):
        resp = xarray_client.get("/api/xarray/tiles/8/0/0.bmp?key=test")
        assert resp.status_code == 400

    def test_xarray_thumbnail_bad_format(self, xarray_client):
        resp = xarray_client.get("/api/xarray/thumbnail.bmp?key=test")
        assert resp.status_code == 400

    def test_xarray_single_dataset_no_key(self, sample_data_array):
        """When only one dataset is registered, key can be omitted."""
        from fastapi.testclient import TestClient

        from localtileserver.web import create_app

        app = create_app()
        reader = XarrayReader(sample_data_array)
        app.state.xarray_registry = {"only_one": reader}
        with TestClient(app) as c:
            resp = c.get("/api/xarray/info")
            assert resp.status_code == 200
