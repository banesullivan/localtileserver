"""Tests for Mosaic support."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from morecantile import tms
import pytest
import rasterio
import rasterio.warp
from rio_tiler.errors import TileOutsideBounds

from localtileserver.examples import get_data_path
from localtileserver.tiler.mosaic import get_mosaic_preview, get_mosaic_tile
from localtileserver.web import create_app


@pytest.fixture
def bahamas_path():
    return str(get_data_path("bahamas_rgb.tif"))


@pytest.fixture
def mosaic_assets(bahamas_path):
    """Use the same file twice to form a trivial mosaic."""
    return [bahamas_path, bahamas_path]


def _get_tile_for_file(path, zoom=10):
    """Find a valid tile covering the given raster file."""
    with rasterio.open(path) as src:
        bounds = rasterio.warp.transform_bounds(src.crs, "EPSG:4326", *src.bounds)
    tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=zoom))
    assert len(tiles) > 0
    return tiles[0]


# --- Mosaic handler ---


def test_mosaic_preview(mosaic_assets):
    result = get_mosaic_preview(mosaic_assets, max_size=64)
    assert result.mimetype == "image/png"
    assert len(bytes(result)) > 0


def test_mosaic_preview_jpeg(mosaic_assets):
    result = get_mosaic_preview(mosaic_assets, img_format="JPEG", max_size=64)
    assert result.mimetype == "image/jpeg"


def test_mosaic_tile(mosaic_assets):
    t = _get_tile_for_file(mosaic_assets[0])
    result = get_mosaic_tile(mosaic_assets, t.z, t.x, t.y)
    assert result.mimetype == "image/png"
    assert len(bytes(result)) > 0


def test_mosaic_tile_with_indexes(mosaic_assets):
    t = _get_tile_for_file(mosaic_assets[0])
    result = get_mosaic_tile(mosaic_assets, t.z, t.x, t.y, indexes=[1])
    assert result.mimetype == "image/png"


# --- Mosaic router ---


@pytest.fixture
def mosaic_client(bahamas_path):
    app = create_app()
    app.state.mosaic_assets = [bahamas_path, bahamas_path]
    with TestClient(app) as c:
        yield c


def test_mosaic_thumbnail_endpoint(mosaic_client):
    resp = mosaic_client.get("/api/mosaic/thumbnail.png?max_size=64")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_mosaic_thumbnail_with_files(mosaic_client, bahamas_path):
    resp = mosaic_client.get(f"/api/mosaic/thumbnail.png?files={bahamas_path}&max_size=64")
    assert resp.status_code == 200


def test_mosaic_tile_endpoint(mosaic_client, bahamas_path):
    t = _get_tile_for_file(bahamas_path)
    resp = mosaic_client.get(f"/api/mosaic/tiles/{t.z}/{t.x}/{t.y}.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_mosaic_bad_format(mosaic_client):
    resp = mosaic_client.get("/api/mosaic/tiles/10/0/0.bmp")
    assert resp.status_code == 400


def test_mosaic_thumbnail_bad_format(mosaic_client):
    resp = mosaic_client.get("/api/mosaic/thumbnail.bmp")
    assert resp.status_code == 400


def test_mosaic_no_files():
    """No files and no app state should return 400."""
    app = create_app()
    with TestClient(app) as c:
        resp = c.get("/api/mosaic/thumbnail.png")
        assert resp.status_code == 400


def test_mosaic_tile_endpoint_with_indexes(mosaic_client, bahamas_path):
    t = _get_tile_for_file(bahamas_path)
    resp = mosaic_client.get(f"/api/mosaic/tiles/{t.z}/{t.x}/{t.y}.png?indexes=1")
    assert resp.status_code == 200


def test_mosaic_tile_endpoint_exception(mosaic_client):
    with patch(
        "localtileserver.web.routers.mosaic.get_mosaic_tile",
        side_effect=RuntimeError("test error"),
    ):
        resp = mosaic_client.get("/api/mosaic/tiles/10/0/0.png")
    assert resp.status_code == 400


def test_mosaic_tile_outside_bounds(mosaic_client):
    with patch(
        "localtileserver.web.routers.mosaic.get_mosaic_tile",
        side_effect=TileOutsideBounds("out"),
    ):
        resp = mosaic_client.get("/api/mosaic/tiles/1/0/0.png")
    assert resp.status_code == 404


def test_mosaic_thumbnail_with_indexes(mosaic_client):
    resp = mosaic_client.get("/api/mosaic/thumbnail.png?indexes=1&max_size=64")
    assert resp.status_code == 200


def test_mosaic_thumbnail_exception(mosaic_client):
    with patch(
        "localtileserver.web.routers.mosaic.get_mosaic_preview",
        side_effect=RuntimeError("preview error"),
    ):
        resp = mosaic_client.get("/api/mosaic/thumbnail.png?max_size=64")
    assert resp.status_code == 400
