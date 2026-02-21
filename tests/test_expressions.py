"""Tests for band math expressions, statistics, stretch modes, output formats, and part/feature."""

import json

import pytest

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


class TestExpressions:
    def test_tile_with_expression(self, reader):
        tile = get_tile(reader, 8, 72, 110, expression="b1")
        assert len(tile) > 0

    def test_tile_multi_band_expression(self, reader):
        tile = get_tile(reader, 8, 72, 110, expression="b3;b2;b1")
        assert len(tile) > 0

    def test_tile_math_expression(self, reader):
        tile = get_tile(reader, 8, 72, 110, expression="(b1-b2)/(b1+b2)", colormap="viridis")
        assert len(tile) > 0

    def test_preview_with_expression(self, reader):
        thumb = get_preview(reader, expression="b1", colormap="viridis")
        assert len(thumb) > 0

    def test_expression_indexes_mutual_exclusion(self):
        from localtileserver.examples import get_bahamas

        client = get_bahamas()
        try:
            with pytest.raises(ValueError, match=r"expression.*indexes|indexes.*expression"):
                client.tile(8, 72, 110, indexes=[1], expression="b1")
        finally:
            client.shutdown(force=True)

    def test_tile_url_with_expression(self):
        from localtileserver.examples import get_bahamas

        client = get_bahamas()
        try:
            url = client.get_tile_url(expression="b1")
            assert "expression=b1" in url
        finally:
            client.shutdown(force=True)


class TestStatistics:
    def test_basic_statistics(self, reader):
        stats = get_statistics(reader)
        assert "b1" in stats
        assert "min" in stats["b1"]
        assert "max" in stats["b1"]

    def test_statistics_single_band(self, reader):
        stats = get_statistics(reader, indexes=[1])
        assert "b1" in stats
        assert len(stats) == 1

    def test_statistics_with_expression(self, reader):
        stats = get_statistics(reader, expression="b1+b2")
        assert len(stats) >= 1

    def test_client_statistics(self):
        from localtileserver.examples import get_bahamas

        client = get_bahamas()
        try:
            stats = client.statistics()
            assert "b1" in stats
        finally:
            client.shutdown(force=True)

    def test_client_statistics_single_band(self):
        from localtileserver.examples import get_bahamas

        client = get_bahamas()
        try:
            stats = client.statistics(indexes=[1])
            assert "b1" in stats
            assert len(stats) == 1
        finally:
            client.shutdown(force=True)


class TestStatisticsEndpoint:
    def test_statistics_endpoint(self, flask_client, bahamas_file):
        r = flask_client.get(f"/api/statistics?filename={bahamas_file}")
        assert r.status_code == 200
        data = r.json()
        assert "b1" in data

    def test_statistics_with_expression(self, flask_client, bahamas_file):
        r = flask_client.get(f"/api/statistics?filename={bahamas_file}&expression=b1")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1


class TestMultipleOutputFormats:
    def test_webp_tile(self, reader):
        tile = get_tile(reader, 8, 72, 110, img_format="WEBP")
        assert len(tile) > 0

    def test_geotiff_tile(self, reader):
        tile = get_tile(reader, 8, 72, 110, img_format="GTiff")
        assert len(tile) > 0

    def test_npy_tile(self, reader):
        tile = get_tile(reader, 8, 72, 110, img_format="NPY")
        assert len(tile) > 0

    def test_webp_thumbnail(self, reader):
        thumb = get_preview(reader, img_format="WEBP")
        assert len(thumb) > 0

    def test_format_to_encoding_new_formats(self):
        from localtileserver.tiler.utilities import format_to_encoding

        assert format_to_encoding("webp") == "WEBP"
        assert format_to_encoding("tif") == "GTiff"
        assert format_to_encoding("tiff") == "GTiff"
        assert format_to_encoding("geotiff") == "GTiff"
        assert format_to_encoding("npy") == "NPY"


class TestStretchModes:
    def test_minmax_stretch(self, reader):
        tile = get_tile(reader, 8, 72, 110, indexes=[1], colormap="viridis", stretch="minmax")
        assert len(tile) > 0

    def test_linear_stretch(self, reader):
        tile = get_tile(reader, 8, 72, 110, indexes=[1], colormap="viridis", stretch="linear")
        assert len(tile) > 0

    def test_sqrt_stretch(self, reader):
        tile = get_tile(reader, 8, 72, 110, indexes=[1], colormap="viridis", stretch="sqrt")
        assert len(tile) > 0

    def test_log_stretch(self, reader):
        tile = get_tile(reader, 8, 72, 110, indexes=[1], colormap="viridis", stretch="log")
        assert len(tile) > 0

    def test_none_stretch(self, reader):
        tile = get_tile(reader, 8, 72, 110, stretch="none")
        assert len(tile) > 0

    def test_invalid_stretch_raises(self, reader):
        with pytest.raises(ValueError, match="Invalid stretch"):
            get_tile(reader, 8, 72, 110, stretch="invalid_mode")

    def test_stretch_endpoint(self, flask_client, bahamas_file):
        r = flask_client.get(
            f"/api/thumbnail.png?filename={bahamas_file}&indexes=1&colormap=viridis&stretch=linear"
        )
        assert r.status_code == 200


class TestPartReads:
    def test_basic_part(self, reader):
        # Use bounds from the bahamas file
        bounds = reader.dataset.bounds
        bbox = (bounds.left, bounds.bottom, bounds.right, bounds.top)
        result = get_part(reader, bbox)
        assert len(result) > 0

    def test_part_with_colormap(self, reader):
        bounds = reader.dataset.bounds
        bbox = (bounds.left, bounds.bottom, bounds.right, bounds.top)
        result = get_part(reader, bbox, indexes=[1], colormap="viridis")
        assert len(result) > 0

    def test_part_endpoint(self, flask_client, bahamas_file):
        from localtileserver.tiler.handler import get_reader as _get_reader

        rdr = _get_reader(bahamas_file)
        b = rdr.dataset.bounds
        bbox_str = f"{b.left},{b.bottom},{b.right},{b.top}"
        r = flask_client.get(f"/api/part.png?filename={bahamas_file}&bbox={bbox_str}")
        assert r.status_code == 200
        assert len(r.content) > 0


class TestFeatureReads:
    def _geo_bounds(self, reader):
        import rasterio.warp

        b = reader.dataset.bounds
        return rasterio.warp.transform_bounds(
            reader.dataset.crs, "EPSG:4326", b.left, b.bottom, b.right, b.top
        )

    def test_basic_feature(self, reader):
        left, bottom, right, top = self._geo_bounds(reader)
        geojson = {
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
        result = get_feature(reader, geojson)
        assert len(result) > 0

    def test_feature_endpoint(self, flask_client, bahamas_file):
        from localtileserver.tiler.handler import get_reader as _get_reader

        rdr = _get_reader(bahamas_file)
        left, bottom, right, top = self._geo_bounds(rdr)
        geojson = {
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
        r = flask_client.post(
            f"/api/feature.png?filename={bahamas_file}",
            content=json.dumps(geojson),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 200
        assert len(r.content) > 0
