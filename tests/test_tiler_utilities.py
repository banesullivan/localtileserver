"""Tests for localtileserver.tiler.utilities."""

import pathlib

import pytest
from rasterio import CRS

from localtileserver.tiler.utilities import (
    ImageBytes,
    format_to_encoding,
    get_cache_dir,
    get_clean_filename,
    make_crs,
    make_vsi,
    purge_cache,
)


class TestImageBytes:
    def test_repr_with_mimetype(self):
        img = ImageBytes(b"\x89PNG...", mimetype="image/png")
        assert "image/png" in repr(img)
        assert "ImageBytes" in repr(img)

    def test_repr_without_mimetype(self):
        img = ImageBytes(b"\x89PNG...")
        assert "wrapped image bytes" in repr(img)

    def test_mimetype_property(self):
        img = ImageBytes(b"data", mimetype="image/jpeg")
        assert img.mimetype == "image/jpeg"

    def test_repr_png(self):
        img = ImageBytes(b"pngdata", mimetype="image/png")
        assert img._repr_png_() == img
        img2 = ImageBytes(b"jpgdata", mimetype="image/jpeg")
        assert img2._repr_png_() is None

    def test_repr_jpeg(self):
        img = ImageBytes(b"jpgdata", mimetype="image/jpeg")
        assert img._repr_jpeg_() == img
        img2 = ImageBytes(b"pngdata", mimetype="image/png")
        assert img2._repr_jpeg_() is None

    def test_bytes_subclass(self):
        img = ImageBytes(b"test")
        assert isinstance(img, bytes)
        assert len(img) == 4


class TestCacheDir:
    def test_get_cache_dir(self):
        d = get_cache_dir()
        assert d.exists()
        assert d.is_dir()

    def test_purge_cache(self):
        d = get_cache_dir()
        # Create a test file
        test_file = d / "test_purge.tmp"
        test_file.touch()
        assert test_file.exists()
        new_d = purge_cache()
        assert new_d.exists()
        assert not test_file.exists()


class TestMakeVsi:
    def test_http_url(self):
        vsi = make_vsi("https://example.com/data.tif")
        assert vsi.startswith("/vsicurl?")
        assert "example.com" in vsi

    def test_s3_url(self):
        vsi = make_vsi("s3://my-bucket/my-key.tif")
        assert vsi == "/vsis3/my-bucket/my-key.tif"


class TestGetCleanFilename:
    def test_example_names(self):
        # These should return valid paths without raising
        get_clean_filename("blue_marble")
        get_clean_filename("virtual_earth")
        get_clean_filename("arcgis")
        get_clean_filename("elevation")
        get_clean_filename("dem")
        get_clean_filename("topo")
        get_clean_filename("bahamas")

    def test_vsi_passthrough(self):
        assert get_clean_filename("/vsicurl/test") == "/vsicurl/test"

    def test_gdal_prefix_passthrough(self):
        assert get_clean_filename("GTI:/path/to/file") == "GTI:/path/to/file"
        assert get_clean_filename("WMTS:url") == "WMTS:url"

    def test_http_url(self):
        result = get_clean_filename("https://example.com/data.tif")
        assert "/vsicurl" in str(result)

    def test_nonexistent_path_raises(self):
        with pytest.raises(OSError, match="Path does not exist"):
            get_clean_filename("/nonexistent/path/to/file.tif")


class TestFormatToEncoding:
    def test_png(self):
        assert format_to_encoding("png") == "PNG"

    def test_jpeg(self):
        assert format_to_encoding("jpeg") == "JPEG"

    def test_jpg(self):
        assert format_to_encoding("jpg") == "JPEG"

    def test_none_default(self):
        assert format_to_encoding(None) == "png"

    def test_empty_default(self):
        assert format_to_encoding("") == "png"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            format_to_encoding("gif")

    def test_case_insensitive(self):
        assert format_to_encoding("PNG") == "PNG"
        assert format_to_encoding("Jpeg") == "JPEG"


class TestMakeCrs:
    def test_from_string(self):
        crs = make_crs("EPSG:4326")
        assert crs == CRS.from_epsg(4326)

    def test_from_int(self):
        crs = make_crs(4326)
        assert crs == CRS.from_epsg(4326)

    def test_from_dict(self):
        crs = make_crs({"init": "EPSG:4326"})
        assert crs is not None
