"""Tests for band math expressions, statistics, stretch modes, output formats, and part/feature."""

import json

import pytest
import rasterio.warp

from localtileserver.examples import get_bahamas
from localtileserver.tiler import format_to_encoding
from localtileserver.tiler.handler import (
    get_feature,
    get_part,
    get_preview,
    get_reader,
    get_statistics,
    get_tile,
)


@pytest.fixture
def reader(bahamas_file):
    return get_reader(bahamas_file)


def _geo_bounds(reader):
    """Transform reader bounds to EPSG:4326."""
    b = reader.dataset.bounds
    return rasterio.warp.transform_bounds(
        reader.dataset.crs, "EPSG:4326", b.left, b.bottom, b.right, b.top
    )


# --- Expressions ---


def test_tile_with_expression(reader, compare):
    tile = get_tile(reader, 8, 72, 110, expression="b1")
    assert len(tile) > 0
    compare(tile)


def test_tile_multi_band_expression(reader, compare):
    tile = get_tile(reader, 8, 72, 110, expression="b3;b2;b1")
    assert len(tile) > 0
    compare(tile)


def test_tile_math_expression(reader, compare):
    tile = get_tile(
        reader, 8, 72, 110, expression="(b3-b1)/(b3+b1)", colormap="viridis", vmin=-0.5, vmax=0.5
    )
    assert len(tile) > 0
    compare(tile)


def test_preview_with_expression(reader, compare):
    thumb = get_preview(reader, expression="b1", colormap="viridis")
    assert len(thumb) > 0
    compare(thumb)


def test_expression_indexes_mutual_exclusion():
    client = get_bahamas()
    try:
        with pytest.raises(ValueError, match=r"expression.*indexes|indexes.*expression"):
            client.tile(8, 72, 110, indexes=[1], expression="b1")
    finally:
        client.shutdown(force=True)


def test_tile_url_with_expression():
    client = get_bahamas()
    try:
        url = client.get_tile_url(expression="b1")
        assert "expression=b1" in url
    finally:
        client.shutdown(force=True)


# --- Statistics ---


def test_basic_statistics(reader):
    stats = get_statistics(reader)
    assert "b1" in stats
    assert "min" in stats["b1"]
    assert "max" in stats["b1"]


def test_statistics_single_band(reader):
    stats = get_statistics(reader, indexes=[1])
    assert "b1" in stats
    assert len(stats) == 1


def test_statistics_with_expression(reader):
    stats = get_statistics(reader, expression="b1+b2")
    assert len(stats) >= 1


def test_client_statistics():
    client = get_bahamas()
    try:
        stats = client.statistics()
        assert "b1" in stats
    finally:
        client.shutdown(force=True)


def test_client_statistics_single_band():
    client = get_bahamas()
    try:
        stats = client.statistics(indexes=[1])
        assert "b1" in stats
        assert len(stats) == 1
    finally:
        client.shutdown(force=True)


# --- Statistics endpoint ---


def test_statistics_endpoint(flask_client, bahamas_file):
    r = flask_client.get(f"/api/statistics?filename={bahamas_file}")
    assert r.status_code == 200
    data = r.json()
    assert "b1" in data


def test_statistics_endpoint_with_expression(flask_client, bahamas_file):
    r = flask_client.get(f"/api/statistics?filename={bahamas_file}&expression=b1")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1


# --- Output formats ---


def test_webp_tile(reader):
    tile = get_tile(reader, 8, 72, 110, img_format="WEBP")
    assert len(tile) > 0


def test_geotiff_tile(reader):
    tile = get_tile(reader, 8, 72, 110, img_format="GTiff")
    assert len(tile) > 0


def test_npy_tile(reader):
    tile = get_tile(reader, 8, 72, 110, img_format="NPY")
    assert len(tile) > 0


def test_webp_thumbnail(reader):
    thumb = get_preview(reader, img_format="WEBP")
    assert len(thumb) > 0


def test_format_to_encoding_new_formats():
    assert format_to_encoding("webp") == "WEBP"
    assert format_to_encoding("tif") == "GTiff"
    assert format_to_encoding("tiff") == "GTiff"
    assert format_to_encoding("geotiff") == "GTiff"
    assert format_to_encoding("npy") == "NPY"


# --- Stretch modes ---


@pytest.mark.parametrize("stretch", ["minmax", "linear", "sqrt", "log"])
def test_stretch_tile(reader, compare, stretch):
    tile = get_tile(reader, 8, 72, 110, indexes=[1], colormap="viridis", stretch=stretch)
    assert len(tile) > 0
    compare(tile)


def test_stretch_none(reader, compare):
    tile = get_tile(reader, 8, 72, 110, stretch="none")
    assert len(tile) > 0
    compare(tile)


def test_stretch_equalize(reader, compare):
    tile = get_tile(reader, 8, 72, 110, indexes=[1], colormap="viridis", stretch="equalize")
    assert len(tile) > 0
    compare(tile)


@pytest.mark.parametrize("stretch", ["minmax", "linear"])
def test_stretch_thumbnail(reader, compare, stretch):
    thumb = get_preview(reader, indexes=[1], colormap="viridis", stretch=stretch)
    assert len(thumb) > 0
    compare(thumb)


def test_invalid_stretch_raises(reader):
    with pytest.raises(ValueError, match="Invalid stretch"):
        get_tile(reader, 8, 72, 110, stretch="invalid_mode")


def test_stretch_endpoint(flask_client, bahamas_file):
    r = flask_client.get(
        f"/api/thumbnail.png?filename={bahamas_file}&indexes=1&colormap=viridis&stretch=linear"
    )
    assert r.status_code == 200


def test_client_stretch_tile():
    client = get_bahamas()
    try:
        tile = client.tile(8, 72, 110, indexes=[1], colormap="viridis", stretch="linear")
        assert len(tile) > 0
    finally:
        client.shutdown(force=True)


def test_client_stretch_thumbnail():
    client = get_bahamas()
    try:
        thumb = client.thumbnail(indexes=[1], colormap="viridis", stretch="minmax")
        assert len(thumb) > 0
    finally:
        client.shutdown(force=True)


def test_client_stretch_tile_url():
    client = get_bahamas()
    try:
        url = client.get_tile_url(stretch="linear")
        assert "stretch=linear" in url
    finally:
        client.shutdown(force=True)


# --- Part reads ---


def test_basic_part(reader, compare):
    bounds = reader.dataset.bounds
    bbox = (bounds.left, bounds.bottom, bounds.right, bounds.top)
    result = get_part(reader, bbox)
    assert len(result) > 0
    compare(result)


def test_part_with_colormap(reader, compare):
    bounds = reader.dataset.bounds
    bbox = (bounds.left, bounds.bottom, bounds.right, bounds.top)
    result = get_part(reader, bbox, indexes=[1], colormap="viridis")
    assert len(result) > 0
    compare(result)


def test_part_endpoint(flask_client, bahamas_file):
    rdr = get_reader(bahamas_file)
    b = rdr.dataset.bounds
    bbox_str = f"{b.left},{b.bottom},{b.right},{b.top}"
    r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox={bbox_str}")
    assert r.status_code == 200
    assert len(r.content) > 0


def test_client_part():
    client = get_bahamas()
    try:
        b = client.bounds()
        bbox = (b[2], b[0], b[3], b[1])
        result = client.part(bbox)
        assert len(result) > 0
    finally:
        client.shutdown(force=True)


def test_client_part_with_colormap():
    client = get_bahamas()
    try:
        b = client.bounds()
        bbox = (b[2], b[0], b[3], b[1])
        result = client.part(bbox, indexes=[1], colormap="viridis")
        assert len(result) > 0
    finally:
        client.shutdown(force=True)


def test_client_part_with_stretch():
    client = get_bahamas()
    try:
        b = client.bounds()
        bbox = (b[2], b[0], b[3], b[1])
        result = client.part(bbox, indexes=[1], colormap="viridis", stretch="linear")
        assert len(result) > 0
    finally:
        client.shutdown(force=True)


# --- Feature reads ---


def _client_geo_bounds(client):
    """Get geographic bounds from a TileClient.

    (south, west, north, east -> left, bottom, right, top).
    """
    b = client.bounds()
    return b[2], b[0], b[3], b[1]


def _make_bbox_geojson(left, bottom, right, top):
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [left, bottom],
                [right, bottom],
                [right, top],
                [left, top],
                [left, bottom],
            ]
        ],
    }


def test_basic_feature(reader, compare):
    left, bottom, right, top = _geo_bounds(reader)
    geojson = _make_bbox_geojson(left, bottom, right, top)
    result = get_feature(reader, geojson)
    assert len(result) > 0
    compare(result)


def test_feature_endpoint(flask_client, bahamas_file):
    rdr = get_reader(bahamas_file)
    left, bottom, right, top = _geo_bounds(rdr)
    geojson = _make_bbox_geojson(left, bottom, right, top)
    r = flask_client.post(
        f"/api/feature.png?filename={bahamas_file}",
        content=json.dumps(geojson),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert len(r.content) > 0


def test_client_feature():
    client = get_bahamas()
    try:
        left, bottom, right, top = _client_geo_bounds(client)
        geojson = _make_bbox_geojson(left, bottom, right, top)
        result = client.feature(geojson)
        assert len(result) > 0
    finally:
        client.shutdown(force=True)


def test_client_feature_with_colormap():
    client = get_bahamas()
    try:
        left, bottom, right, top = _client_geo_bounds(client)
        geojson = _make_bbox_geojson(left, bottom, right, top)
        result = client.feature(geojson, indexes=[1], colormap="viridis")
        assert len(result) > 0
    finally:
        client.shutdown(force=True)


def test_client_feature_with_stretch():
    client = get_bahamas()
    try:
        left, bottom, right, top = _client_geo_bounds(client)
        geojson = _make_bbox_geojson(left, bottom, right, top)
        result = client.feature(geojson, indexes=[1], colormap="viridis", stretch="linear")
        assert len(result) > 0
    finally:
        client.shutdown(force=True)
