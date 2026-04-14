"""Tests for error-handling paths in the tiles router."""

from unittest.mock import patch

from rasterio import RasterioIOError
from rio_tiler.errors import TileOutsideBounds

GEOJSON_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[-78, 24], [-77, 24], [-77, 25], [-78, 25], [-78, 24]]],
}


# --- Invalid format → 400 ---


def test_thumbnail_invalid_format(flask_client, bahamas_file):
    r = flask_client.get(f"/api/thumbnail.xyz?filename={bahamas_file}")
    assert r.status_code == 400
    assert "not a valid encoding" in r.json()["detail"]


def test_part_invalid_format(flask_client, bahamas_file):
    r = flask_client.get(f"/api/part.xyz?filename={bahamas_file}&bbox=-78,24,-77,25")
    assert r.status_code == 400
    assert "not a valid encoding" in r.json()["detail"]


def test_feature_invalid_format(flask_client, bahamas_file):
    r = flask_client.post(f"/api/feature.xyz?filename={bahamas_file}", json=GEOJSON_POLYGON)
    assert r.status_code == 400
    assert "not a valid encoding" in r.json()["detail"]


# --- Invalid bbox → 400 ---


def test_part_invalid_bbox_non_numeric(flask_client, bahamas_file):
    r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox=a,b,c,d")
    assert r.status_code == 400
    assert "4 comma-separated floats" in r.json()["detail"]


def test_part_invalid_bbox_wrong_count(flask_client, bahamas_file):
    r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox=1.0,2.0,3.0")
    assert r.status_code == 400
    assert "4 comma-separated floats" in r.json()["detail"]


def test_part_invalid_bbox_empty(flask_client, bahamas_file):
    r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox=")
    assert r.status_code == 400
    assert "4 comma-separated floats" in r.json()["detail"]


# --- RasterioIOError → 500 ---


def test_thumbnail_rasterio_io_error(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_preview",
        side_effect=RasterioIOError("disk error"),
    ):
        r = flask_client.get(f"/api/thumbnail.png?filename={bahamas_file}")
    assert r.status_code == 500
    assert "Rasterio error" in r.json()["detail"]


def test_tile_rasterio_io_error(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_tile",
        side_effect=RasterioIOError("disk error"),
    ):
        r = flask_client.get(f"/api/tiles/8/72/110.png?filename={bahamas_file}")
    assert r.status_code == 500
    assert "Rasterio error" in r.json()["detail"]


def test_part_rasterio_io_error(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_part",
        side_effect=RasterioIOError("disk error"),
    ):
        r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox=-78,24,-77,25")
    assert r.status_code == 500
    assert "Rasterio error" in r.json()["detail"]


def test_feature_rasterio_io_error(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_feature",
        side_effect=RasterioIOError("disk error"),
    ):
        r = flask_client.post(f"/api/feature.png?filename={bahamas_file}", json=GEOJSON_POLYGON)
    assert r.status_code == 500
    assert "Rasterio error" in r.json()["detail"]


# --- Generic Exception → 500 ---


def test_thumbnail_generic_exception(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_preview",
        side_effect=RuntimeError("unexpected"),
    ):
        r = flask_client.get(f"/api/thumbnail.png?filename={bahamas_file}")
    assert r.status_code == 500
    assert "rendering error" in r.json()["detail"]


def test_tile_generic_exception(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_tile",
        side_effect=RuntimeError("unexpected"),
    ):
        r = flask_client.get(f"/api/tiles/8/72/110.png?filename={bahamas_file}")
    assert r.status_code == 500
    assert "rendering error" in r.json()["detail"]


def test_part_generic_exception(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_part",
        side_effect=RuntimeError("unexpected"),
    ):
        r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox=-78,24,-77,25")
    assert r.status_code == 500
    assert "rendering error" in r.json()["detail"]


def test_feature_generic_exception(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_feature",
        side_effect=RuntimeError("unexpected"),
    ):
        r = flask_client.post(f"/api/feature.png?filename={bahamas_file}", json=GEOJSON_POLYGON)
    assert r.status_code == 500
    assert "rendering error" in r.json()["detail"]


# --- TileOutsideBounds → 404 ---


def test_tile_outside_bounds(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_tile",
        side_effect=TileOutsideBounds("out of bounds"),
    ):
        r = flask_client.get(f"/api/tiles/1/0/0.png?filename={bahamas_file}")
    assert r.status_code == 404
    assert "outside bounds" in r.json()["detail"]


# --- _get_reader errors → 400 ---


def test_get_reader_oserror(flask_client):
    with patch(
        "localtileserver.tiler.utilities.get_clean_filename",
        side_effect=OSError("Path does not exist"),
    ):
        r = flask_client.get("/api/metadata?filename=bogus.tif")
    assert r.status_code == 400
    assert "Path does not exist" in r.json()["detail"]


def test_get_reader_rasterio_io_error(flask_client, bahamas_file):
    with patch(
        "localtileserver.web.routers.tiles.get_reader",
        side_effect=RasterioIOError("cannot open"),
    ):
        r = flask_client.get(f"/api/metadata?filename={bahamas_file}")
    assert r.status_code == 400
    assert "RasterioIOError" in r.json()["detail"]


# --- Invalid COG → 415 ---


def test_validate_cog_invalid(flask_client, bahamas_file):
    with patch("localtileserver.validate.validate_cog", return_value=False):
        r = flask_client.get(f"/api/validate?filename={bahamas_file}")
    assert r.status_code == 415
    assert "Not a valid Cloud Optimized GeoTiff" in r.json()["detail"]
