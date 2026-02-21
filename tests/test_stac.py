"""Tests for STAC reader support (Phase 3.1)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from rio_tiler.models import BandStatistics, ImageData, Info


def _make_image_data(count=3, height=256, width=256):
    """Create a synthetic ImageData for mocking."""
    data = np.random.randint(0, 255, (count, height, width), dtype=np.uint8)
    return ImageData(data)


def _make_info():
    """Create a minimal Info object for mocking."""
    return Info(
        bounds=(-180, -90, 180, 90),
        crs="http://www.opengis.net/def/crs/OGC/1.3/CRS84",
        band_metadata=[("b1", {})],
        band_descriptions=[("b1", "red")],
        dtype="uint8",
        nodata_type="None",
        colorinterp=None,
        driver=None,
        count=1,
        width=256,
        height=256,
    )


def _make_band_stats():
    return BandStatistics(
        min=0.0,
        max=255.0,
        mean=127.0,
        count=65536,
        sum=8323072.0,
        std=73.0,
        median=127.0,
        majority=0.0,
        minority=255.0,
        unique=256,
        histogram=[
            [256] * 10,
            list(np.linspace(0, 255, 11)),
        ],
        valid_percent=100.0,
        masked_pixels=0,
        valid_pixels=65536,
        percentile_2=5.0,
        percentile_98=250.0,
    )


@pytest.fixture
def mock_stac_reader():
    """Create a mock STACReader."""
    with patch("localtileserver.tiler.stac.STACReader") as MockReader:
        reader = MagicMock()
        reader.info.return_value = {"visual": _make_info()}
        reader.statistics.return_value = {"visual_b1": _make_band_stats()}
        reader.tile.return_value = _make_image_data()
        reader.preview.return_value = _make_image_data()
        reader.bounds = (-180, -90, 180, 90)
        reader.crs = "EPSG:4326"
        reader.assets = ["visual", "B04", "B03", "B02"]
        MockReader.return_value = reader
        yield reader, MockReader


class TestStacHandler:
    def test_get_stac_reader(self, mock_stac_reader):
        reader, MockReader = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_reader

        result = get_stac_reader("https://example.com/stac/item.json")
        MockReader.assert_called_once_with("https://example.com/stac/item.json")
        assert result is reader

    def test_get_stac_info(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_info

        result = get_stac_info(reader, assets=["visual"])
        reader.info.assert_called_once_with(assets=["visual"])
        assert "visual" in result

    def test_get_stac_info_no_assets(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_info

        result = get_stac_info(reader)
        reader.info.assert_called_once_with()
        assert isinstance(result, dict)

    def test_get_stac_statistics(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_statistics

        result = get_stac_statistics(reader, assets=["visual"])
        reader.statistics.assert_called_once_with(assets=["visual"])
        assert "visual_b1" in result

    def test_get_stac_tile(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_tile

        result = get_stac_tile(reader, z=10, x=512, y=512, assets=["visual"])
        reader.tile.assert_called_once_with(512, 512, 10, assets=["visual"])
        assert result.mimetype == "image/png"
        assert len(bytes(result)) > 0

    def test_get_stac_tile_with_expression(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_tile

        result = get_stac_tile(
            reader, z=10, x=512, y=512,
            expression="(B04-B03)/(B04+B03)",
        )
        reader.tile.assert_called_once_with(
            512, 512, 10, expression="(B04-B03)/(B04+B03)"
        )
        assert result.mimetype == "image/png"

    def test_get_stac_tile_jpeg(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_tile

        result = get_stac_tile(reader, z=10, x=512, y=512, img_format="JPEG")
        assert result.mimetype == "image/jpeg"

    def test_get_stac_preview(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_preview

        result = get_stac_preview(reader, assets=["visual"], max_size=256)
        reader.preview.assert_called_once_with(max_size=256, assets=["visual"])
        assert result.mimetype == "image/png"

    def test_get_stac_preview_with_expression(self, mock_stac_reader):
        reader, _ = mock_stac_reader
        from localtileserver.tiler.stac import get_stac_preview

        result = get_stac_preview(
            reader, expression="(B04-B03)/(B04+B03)", max_size=128
        )
        reader.preview.assert_called_once_with(
            max_size=128, expression="(B04-B03)/(B04+B03)"
        )
        assert result.mimetype == "image/png"


class TestStacRouter:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from localtileserver.web import create_app

        app = create_app()
        with TestClient(app) as c:
            yield c

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_info_endpoint(self, mock_get_reader, client):
        reader = MagicMock()
        reader.info.return_value = {"visual": _make_info()}
        mock_get_reader.return_value = reader

        resp = client.get("/api/stac/info?url=https://example.com/item.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "visual" in data

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_info_with_assets(self, mock_get_reader, client):
        reader = MagicMock()
        reader.info.return_value = {"B04": _make_info()}
        mock_get_reader.return_value = reader

        resp = client.get("/api/stac/info?url=https://example.com/item.json&assets=B04")
        assert resp.status_code == 200

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_info_bad_url(self, mock_get_reader, client):
        mock_get_reader.side_effect = Exception("Failed to fetch")
        resp = client.get("/api/stac/info?url=https://bad.example.com/item.json")
        assert resp.status_code == 400

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_statistics_endpoint(self, mock_get_reader, client):
        reader = MagicMock()
        reader.statistics.return_value = {"visual_b1": _make_band_stats()}
        mock_get_reader.return_value = reader

        resp = client.get("/api/stac/statistics?url=https://example.com/item.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "visual_b1" in data

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_tile_endpoint(self, mock_get_reader, client):
        reader = MagicMock()
        reader.tile.return_value = _make_image_data()
        mock_get_reader.return_value = reader

        resp = client.get(
            "/api/stac/tiles/10/512/512.png?url=https://example.com/item.json&assets=visual"
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_tile_bad_format(self, mock_get_reader, client):
        mock_get_reader.return_value = MagicMock()
        resp = client.get(
            "/api/stac/tiles/10/512/512.bmp?url=https://example.com/item.json"
        )
        assert resp.status_code == 400

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_tile_outside_bounds(self, mock_get_reader, client):
        from rio_tiler.errors import TileOutsideBounds

        reader = MagicMock()
        reader.tile.side_effect = TileOutsideBounds("outside")
        mock_get_reader.return_value = reader

        resp = client.get(
            "/api/stac/tiles/10/512/512.png?url=https://example.com/item.json&assets=visual"
        )
        assert resp.status_code == 404

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_thumbnail_endpoint(self, mock_get_reader, client):
        reader = MagicMock()
        reader.preview.return_value = _make_image_data()
        mock_get_reader.return_value = reader

        resp = client.get(
            "/api/stac/thumbnail.png?url=https://example.com/item.json&assets=visual"
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_thumbnail_bad_format(self, mock_get_reader, client):
        mock_get_reader.return_value = MagicMock()
        resp = client.get(
            "/api/stac/thumbnail.bmp?url=https://example.com/item.json"
        )
        assert resp.status_code == 400

    @patch("localtileserver.web.routers.stac.get_stac_reader")
    def test_stac_thumbnail_bad_url(self, mock_get_reader, client):
        mock_get_reader.side_effect = Exception("Failed to fetch")
        resp = client.get(
            "/api/stac/thumbnail.png?url=https://bad.example.com/item.json"
        )
        assert resp.status_code == 400


class TestParseAssets:
    def test_parse_none(self):
        from localtileserver.web.routers.stac import _parse_assets

        assert _parse_assets(None) is None

    def test_parse_empty(self):
        from localtileserver.web.routers.stac import _parse_assets

        assert _parse_assets("") is None

    def test_parse_single(self):
        from localtileserver.web.routers.stac import _parse_assets

        assert _parse_assets("visual") == ["visual"]

    def test_parse_multiple(self):
        from localtileserver.web.routers.stac import _parse_assets

        assert _parse_assets("B04,B03,B02") == ["B04", "B03", "B02"]

    def test_parse_with_spaces(self):
        from localtileserver.web.routers.stac import _parse_assets

        assert _parse_assets("B04, B03, B02") == ["B04", "B03", "B02"]
