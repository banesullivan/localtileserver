"""Tests for Mosaic support (Phase 3.3)."""

import pytest

from localtileserver.examples import get_data_path
from localtileserver.tiler.mosaic import get_mosaic_preview, get_mosaic_tile


@pytest.fixture
def bahamas_path():
    return str(get_data_path("bahamas_rgb.tif"))


@pytest.fixture
def mosaic_assets(bahamas_path):
    """Use the same file twice to form a trivial mosaic."""
    return [bahamas_path, bahamas_path]


class TestMosaicHandler:
    def test_mosaic_preview(self, mosaic_assets):
        result = get_mosaic_preview(mosaic_assets, max_size=64)
        assert result.mimetype == "image/png"
        assert len(bytes(result)) > 0

    def test_mosaic_preview_jpeg(self, mosaic_assets):
        result = get_mosaic_preview(mosaic_assets, img_format="JPEG", max_size=64)
        assert result.mimetype == "image/jpeg"

    def test_mosaic_tile(self, mosaic_assets):
        import rasterio
        from morecantile import tms

        # Find a valid tile for the bahamas data
        with rasterio.open(mosaic_assets[0]) as src:
            bounds = rasterio.warp.transform_bounds(
                src.crs, "EPSG:4326", *src.bounds
            )
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=10))
        assert len(tiles) > 0
        t = tiles[0]
        result = get_mosaic_tile(mosaic_assets, t.z, t.x, t.y)
        assert result.mimetype == "image/png"
        assert len(bytes(result)) > 0

    def test_mosaic_tile_with_indexes(self, mosaic_assets):
        import rasterio
        from morecantile import tms

        with rasterio.open(mosaic_assets[0]) as src:
            bounds = rasterio.warp.transform_bounds(
                src.crs, "EPSG:4326", *src.bounds
            )
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=10))
        t = tiles[0]
        result = get_mosaic_tile(mosaic_assets, t.z, t.x, t.y, indexes=[1])
        assert result.mimetype == "image/png"


class TestMosaicRouter:
    @pytest.fixture
    def client(self, bahamas_path):
        from fastapi.testclient import TestClient

        from localtileserver.web import create_app

        app = create_app()
        app.state.mosaic_assets = [bahamas_path, bahamas_path]
        with TestClient(app) as c:
            yield c

    def test_mosaic_thumbnail_endpoint(self, client):
        resp = client.get("/api/mosaic/thumbnail.png?max_size=64")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_mosaic_thumbnail_with_files(self, client, bahamas_path):
        resp = client.get(f"/api/mosaic/thumbnail.png?files={bahamas_path}&max_size=64")
        assert resp.status_code == 200

    def test_mosaic_tile_endpoint(self, client, bahamas_path):
        import rasterio
        from morecantile import tms

        with rasterio.open(bahamas_path) as src:
            bounds = rasterio.warp.transform_bounds(
                src.crs, "EPSG:4326", *src.bounds
            )
        tiles = list(tms.get("WebMercatorQuad").tiles(*bounds, zooms=10))
        t = tiles[0]
        resp = client.get(f"/api/mosaic/tiles/{t.z}/{t.x}/{t.y}.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    def test_mosaic_bad_format(self, client):
        resp = client.get("/api/mosaic/tiles/10/0/0.bmp")
        assert resp.status_code == 400

    def test_mosaic_thumbnail_bad_format(self, client):
        resp = client.get("/api/mosaic/thumbnail.bmp")
        assert resp.status_code == 400

    def test_mosaic_no_files(self):
        """No files and no app state should return 400."""
        from fastapi.testclient import TestClient

        from localtileserver.web import create_app

        app = create_app()
        with TestClient(app) as c:
            resp = c.get("/api/mosaic/thumbnail.png")
            assert resp.status_code == 400
