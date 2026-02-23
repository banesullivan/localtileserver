"""Tests for Xarray/DataArray support."""

import numpy as np
import pytest

xr = pytest.importorskip("xarray")
rioxarray = pytest.importorskip("rioxarray")

from fastapi.testclient import TestClient  # noqa: E402
from morecantile import tms  # noqa: E402
from rio_tiler.io.xarray import XarrayReader  # noqa: E402

from localtileserver.tiler.xarray_handler import (  # noqa: E402
    _check_xarray,
    get_xarray_info,
    get_xarray_preview,
    get_xarray_reader,
    get_xarray_statistics,
    get_xarray_tile,
)
from localtileserver.web import create_app  # noqa: E402


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


@pytest.fixture
def xarray_client(sample_data_array):
    app = create_app()
    reader = XarrayReader(sample_data_array)
    if not hasattr(app.state, "xarray_registry"):
        app.state.xarray_registry = {}
    app.state.xarray_registry["test"] = reader
    with TestClient(app) as c:
        yield c


def _get_tile_for_reader(reader, zoom=8):
    """Find a valid tile covering the reader bounds."""
    bounds = reader.bounds
    tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=zoom))
    assert len(tiles) > 0
    return tiles[0]


# --- check_xarray ---


def test_check_xarray():
    # Should not raise when xarray is installed
    _check_xarray()


# --- Reader ---


def test_get_xarray_reader(sample_data_array):
    reader = get_xarray_reader(sample_data_array)
    assert isinstance(reader, XarrayReader)


def test_xarray_reader_has_bounds(sample_data_array):
    reader = get_xarray_reader(sample_data_array)
    assert reader.bounds is not None
    assert len(reader.bounds) == 4


def test_xarray_reader_has_crs(sample_data_array):
    reader = get_xarray_reader(sample_data_array)
    assert reader.crs is not None


# --- Info ---


def test_xarray_info_returns_dict(sample_reader):
    info = get_xarray_info(sample_reader)
    assert isinstance(info, dict)
    assert "bounds" in info
    assert "crs" in info
    assert "dtype" in info


# --- Statistics ---


def test_xarray_statistics(sample_reader):
    stats = get_xarray_statistics(sample_reader)
    assert isinstance(stats, dict)
    assert len(stats) > 0
    for _key, val in stats.items():
        assert "min" in val
        assert "max" in val
        assert "mean" in val


def test_xarray_statistics_with_indexes(sample_reader):
    stats = get_xarray_statistics(sample_reader, indexes=[1])
    assert len(stats) == 1


# --- Tile ---


def test_xarray_tile(sample_reader):
    t = _get_tile_for_reader(sample_reader)
    result = get_xarray_tile(sample_reader, t.z, t.x, t.y)
    assert result.mimetype == "image/png"
    assert len(bytes(result)) > 0


def test_xarray_tile_jpeg(sample_reader):
    t = _get_tile_for_reader(sample_reader)
    result = get_xarray_tile(sample_reader, t.z, t.x, t.y, img_format="JPEG")
    assert result.mimetype == "image/jpeg"


def test_xarray_tile_with_indexes(sample_reader):
    t = _get_tile_for_reader(sample_reader)
    result = get_xarray_tile(sample_reader, t.z, t.x, t.y, indexes=[1])
    assert result.mimetype == "image/png"


# --- Preview ---


def test_xarray_preview(sample_reader):
    result = get_xarray_preview(sample_reader)
    assert result.mimetype == "image/png"
    assert len(bytes(result)) > 0


def test_xarray_preview_with_max_size(sample_reader):
    result = get_xarray_preview(sample_reader, max_size=32)
    assert result.mimetype == "image/png"
    assert len(bytes(result)) > 0


def test_xarray_preview_jpeg(sample_reader):
    result = get_xarray_preview(sample_reader, img_format="JPEG")
    assert result.mimetype == "image/jpeg"


def test_xarray_preview_with_indexes(sample_reader):
    result = get_xarray_preview(sample_reader, indexes=[1, 2])
    assert result.mimetype == "image/png"


# --- Single band ---


def test_single_band_reader(single_band_data_array):
    reader = get_xarray_reader(single_band_data_array)
    assert reader is not None


def test_single_band_info(single_band_data_array):
    reader = get_xarray_reader(single_band_data_array)
    info = get_xarray_info(reader)
    assert info["count"] == 1


def test_single_band_preview(single_band_data_array):
    reader = get_xarray_reader(single_band_data_array)
    result = get_xarray_preview(reader)
    assert result.mimetype == "image/png"


# --- Xarray router ---


def test_xarray_info_endpoint(xarray_client):
    resp = xarray_client.get("/api/xarray/info?key=test")
    assert resp.status_code == 200
    data = resp.json()
    assert "bounds" in data
    assert "crs" in data


def test_xarray_statistics_endpoint(xarray_client):
    resp = xarray_client.get("/api/xarray/statistics?key=test")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0


def test_xarray_thumbnail_endpoint(xarray_client):
    resp = xarray_client.get("/api/xarray/thumbnail.png?key=test")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_xarray_tile_endpoint(xarray_client, sample_data_array):
    reader = XarrayReader(sample_data_array)
    t = _get_tile_for_reader(reader)
    resp = xarray_client.get(f"/api/xarray/tiles/{t.z}/{t.x}/{t.y}.png?key=test")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_xarray_no_registry():
    app = create_app()
    with TestClient(app) as c:
        resp = c.get("/api/xarray/info")
        assert resp.status_code == 400


def test_xarray_key_not_found(xarray_client):
    resp = xarray_client.get("/api/xarray/info?key=nonexistent")
    assert resp.status_code == 404


def test_xarray_bad_format(xarray_client):
    resp = xarray_client.get("/api/xarray/tiles/8/0/0.bmp?key=test")
    assert resp.status_code == 400


def test_xarray_thumbnail_bad_format(xarray_client):
    resp = xarray_client.get("/api/xarray/thumbnail.bmp?key=test")
    assert resp.status_code == 400


def test_xarray_single_dataset_no_key(sample_data_array):
    """When only one dataset is registered, key can be omitted."""
    app = create_app()
    reader = XarrayReader(sample_data_array)
    app.state.xarray_registry = {"only_one": reader}
    with TestClient(app) as c:
        resp = c.get("/api/xarray/info")
        assert resp.status_code == 200
