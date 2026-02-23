"""Tests for STAC reader support."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import numpy as np
import pytest
from rio_tiler.errors import TileOutsideBounds
from rio_tiler.models import BandStatistics, ImageData, Info

from localtileserver.client import STACClient, get_or_create_tile_client
from localtileserver.tiler.stac import (
    get_stac_info,
    get_stac_preview,
    get_stac_reader,
    get_stac_statistics,
    get_stac_tile,
)
from localtileserver.web import create_app
from localtileserver.web.routers.stac import _parse_assets


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


@pytest.fixture
def stac_client():
    app = create_app()
    with TestClient(app) as c:
        yield c


# --- STAC handler ---


def test_get_stac_reader(mock_stac_reader):
    reader, MockReader = mock_stac_reader
    result = get_stac_reader("https://example.com/stac/item.json")
    MockReader.assert_called_once_with("https://example.com/stac/item.json")
    assert result is reader


def test_get_stac_info(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_info(reader, assets=["visual"])
    reader.info.assert_called_once_with(assets=["visual"])
    assert "visual" in result


def test_get_stac_info_no_assets(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_info(reader)
    reader.info.assert_called_once_with()
    assert isinstance(result, dict)


def test_get_stac_statistics(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_statistics(reader, assets=["visual"])
    reader.statistics.assert_called_once_with(assets=["visual"])
    assert "visual_b1" in result


def test_get_stac_tile(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_tile(reader, z=10, x=512, y=512, assets=["visual"])
    reader.tile.assert_called_once_with(512, 512, 10, assets=["visual"])
    assert result.mimetype == "image/png"
    assert len(bytes(result)) > 0


def test_get_stac_tile_with_expression(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_tile(
        reader,
        z=10,
        x=512,
        y=512,
        expression="(B04-B03)/(B04+B03)",
    )
    reader.tile.assert_called_once_with(512, 512, 10, expression="(B04-B03)/(B04+B03)")
    assert result.mimetype == "image/png"


def test_get_stac_tile_jpeg(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_tile(reader, z=10, x=512, y=512, img_format="JPEG")
    assert result.mimetype == "image/jpeg"


def test_get_stac_preview(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_preview(reader, assets=["visual"], max_size=256)
    reader.preview.assert_called_once_with(max_size=256, assets=["visual"])
    assert result.mimetype == "image/png"


def test_get_stac_preview_with_expression(mock_stac_reader):
    reader, _ = mock_stac_reader
    result = get_stac_preview(reader, expression="(B04-B03)/(B04+B03)", max_size=128)
    reader.preview.assert_called_once_with(max_size=128, expression="(B04-B03)/(B04+B03)")
    assert result.mimetype == "image/png"


# --- STAC router ---


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_info_endpoint(mock_get_reader, stac_client):
    reader = MagicMock()
    reader.info.return_value = {"visual": _make_info()}
    mock_get_reader.return_value = reader

    resp = stac_client.get("/api/stac/info?url=https://example.com/item.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "visual" in data


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_info_with_assets(mock_get_reader, stac_client):
    reader = MagicMock()
    reader.info.return_value = {"B04": _make_info()}
    mock_get_reader.return_value = reader

    resp = stac_client.get("/api/stac/info?url=https://example.com/item.json&assets=B04")
    assert resp.status_code == 200


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_info_bad_url(mock_get_reader, stac_client):
    mock_get_reader.side_effect = Exception("Failed to fetch")
    resp = stac_client.get("/api/stac/info?url=https://bad.example.com/item.json")
    assert resp.status_code == 400


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_statistics_endpoint(mock_get_reader, stac_client):
    reader = MagicMock()
    reader.statistics.return_value = {"visual_b1": _make_band_stats()}
    mock_get_reader.return_value = reader

    resp = stac_client.get("/api/stac/statistics?url=https://example.com/item.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "visual_b1" in data


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_tile_endpoint(mock_get_reader, stac_client):
    reader = MagicMock()
    reader.tile.return_value = _make_image_data()
    mock_get_reader.return_value = reader

    resp = stac_client.get(
        "/api/stac/tiles/10/512/512.png?url=https://example.com/item.json&assets=visual"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_tile_bad_format(mock_get_reader, stac_client):
    mock_get_reader.return_value = MagicMock()
    resp = stac_client.get("/api/stac/tiles/10/512/512.bmp?url=https://example.com/item.json")
    assert resp.status_code == 400


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_tile_outside_bounds(mock_get_reader, stac_client):
    reader = MagicMock()
    reader.tile.side_effect = TileOutsideBounds("outside")
    mock_get_reader.return_value = reader

    resp = stac_client.get(
        "/api/stac/tiles/10/512/512.png?url=https://example.com/item.json&assets=visual"
    )
    assert resp.status_code == 404


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_thumbnail_endpoint(mock_get_reader, stac_client):
    reader = MagicMock()
    reader.preview.return_value = _make_image_data()
    mock_get_reader.return_value = reader

    resp = stac_client.get(
        "/api/stac/thumbnail.png?url=https://example.com/item.json&assets=visual"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_thumbnail_bad_format(mock_get_reader, stac_client):
    mock_get_reader.return_value = MagicMock()
    resp = stac_client.get("/api/stac/thumbnail.bmp?url=https://example.com/item.json")
    assert resp.status_code == 400


@patch("localtileserver.web.routers.stac.get_stac_reader")
def test_stac_thumbnail_bad_url(mock_get_reader, stac_client):
    mock_get_reader.side_effect = Exception("Failed to fetch")
    resp = stac_client.get("/api/stac/thumbnail.png?url=https://bad.example.com/item.json")
    assert resp.status_code == 400


# --- _parse_assets helper ---


def test_parse_assets_none():
    assert _parse_assets(None) is None


def test_parse_assets_empty():
    assert _parse_assets("") is None


def test_parse_assets_single():
    assert _parse_assets("visual") == ["visual"]


def test_parse_assets_multiple():
    assert _parse_assets("B04,B03,B02") == ["B04", "B03", "B02"]


def test_parse_assets_with_spaces():
    assert _parse_assets("B04, B03, B02") == ["B04", "B03", "B02"]


# --- STACClient ---


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_bounds(MockReader):
    reader = MagicMock()
    reader.bounds = (-180, -90, 180, 90)
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json")
    try:
        b = client.bounds()
        assert b == (-90, 90, -180, 180)
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_center(MockReader):
    reader = MagicMock()
    reader.bounds = (-180, -90, 180, 90)
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json")
    try:
        c = client.center()
        assert c == (0.0, 0.0)
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_tile(MockReader):
    reader = MagicMock()
    reader.tile.return_value = _make_image_data()
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json", assets=["visual"])
    try:
        result = client.tile(10, 512, 512)
        assert len(bytes(result)) > 0
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_thumbnail(MockReader):
    reader = MagicMock()
    reader.preview.return_value = _make_image_data()
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json", assets=["visual"])
    try:
        result = client.thumbnail()
        assert len(bytes(result)) > 0
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_statistics(MockReader):
    reader = MagicMock()
    reader.statistics.return_value = {"visual_b1": _make_band_stats()}
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json", assets=["visual"])
    try:
        result = client.statistics()
        assert "visual_b1" in result
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_info(MockReader):
    reader = MagicMock()
    reader.info.return_value = {"visual": _make_info()}
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json", assets=["visual"])
    try:
        result = client.stac_info()
        assert "visual" in result
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_get_tile_url(MockReader):
    reader = MagicMock()
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json", assets=["visual"])
    try:
        url = client.get_tile_url()
        assert "api/stac/tiles" in url
        assert "assets=visual" in url
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_get_tile_url_expression(MockReader):
    reader = MagicMock()
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json", expression="B04/B03")
    try:
        url = client.get_tile_url()
        assert "expression=B04" in url
    finally:
        client.shutdown(force=True)


@patch("localtileserver.tiler.stac.STACReader")
def test_stac_client_get_or_create_passthrough(MockReader):
    reader = MagicMock()
    MockReader.return_value = reader

    client = STACClient("https://example.com/stac/item.json")
    try:
        result, created = get_or_create_tile_client(client)
        assert result is client
        assert created is False
    finally:
        client.shutdown(force=True)
