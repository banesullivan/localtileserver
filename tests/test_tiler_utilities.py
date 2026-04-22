"""Tests for localtileserver.tiler.utilities."""

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

# --- ImageBytes ---


def test_image_bytes_repr_with_mimetype():
    img = ImageBytes(b"\x89PNG...", mimetype="image/png")
    assert "image/png" in repr(img)
    assert "ImageBytes" in repr(img)


def test_image_bytes_repr_without_mimetype():
    img = ImageBytes(b"\x89PNG...")
    assert "wrapped image bytes" in repr(img)


def test_image_bytes_mimetype_property():
    img = ImageBytes(b"data", mimetype="image/jpeg")
    assert img.mimetype == "image/jpeg"


def test_image_bytes_repr_png():
    img = ImageBytes(b"pngdata", mimetype="image/png")
    assert img._repr_png_() == img
    img2 = ImageBytes(b"jpgdata", mimetype="image/jpeg")
    assert img2._repr_png_() is None


def test_image_bytes_repr_jpeg():
    img = ImageBytes(b"jpgdata", mimetype="image/jpeg")
    assert img._repr_jpeg_() == img
    img2 = ImageBytes(b"pngdata", mimetype="image/png")
    assert img2._repr_jpeg_() is None


def test_image_bytes_subclass():
    img = ImageBytes(b"test")
    assert isinstance(img, bytes)
    assert len(img) == 4


# --- Cache ---


def test_get_cache_dir():
    d = get_cache_dir()
    assert d.exists()
    assert d.is_dir()


def test_purge_cache():
    d = get_cache_dir()
    # Create a test file
    test_file = d / "test_purge.tmp"
    test_file.touch()
    assert test_file.exists()
    new_d = purge_cache()
    assert new_d.exists()
    assert not test_file.exists()


# --- make_vsi ---


def test_make_vsi_http():
    vsi = make_vsi("https://example.com/data.tif")
    assert vsi.startswith("/vsicurl?")
    assert "example.com" in vsi


def test_make_vsi_s3():
    vsi = make_vsi("s3://my-bucket/my-key.tif")
    assert vsi == "/vsis3/my-bucket/my-key.tif"


# --- get_clean_filename ---


def test_clean_filename_examples():
    # These should return valid paths without raising
    get_clean_filename("blue_marble")
    get_clean_filename("virtual_earth")
    get_clean_filename("arcgis")
    get_clean_filename("elevation")
    get_clean_filename("dem")
    get_clean_filename("topo")
    get_clean_filename("bahamas")


def test_clean_filename_vsi_passthrough():
    assert get_clean_filename("/vsicurl/test") == "/vsicurl/test"


def test_clean_filename_gdal_prefix_passthrough():
    assert get_clean_filename("GTI:/path/to/file") == "GTI:/path/to/file"
    assert get_clean_filename("WMTS:url") == "WMTS:url"


def test_clean_filename_http_url():
    result = get_clean_filename("https://example.com/data.tif")
    assert "/vsicurl" in str(result)


def test_clean_filename_nonexistent_raises():
    with pytest.raises(OSError, match="Path does not exist"):
        get_clean_filename("/nonexistent/path/to/file.tif")


# --- format_to_encoding ---


def test_format_to_encoding_png():
    assert format_to_encoding("png") == "PNG"


def test_format_to_encoding_jpeg():
    assert format_to_encoding("jpeg") == "JPEG"


def test_format_to_encoding_jpg():
    assert format_to_encoding("jpg") == "JPEG"


def test_format_to_encoding_none_default():
    assert format_to_encoding(None) == "png"


def test_format_to_encoding_empty_default():
    assert format_to_encoding("") == "png"


def test_format_to_encoding_invalid_raises():
    with pytest.raises(ValueError):
        format_to_encoding("gif")


def test_format_to_encoding_case_insensitive():
    assert format_to_encoding("PNG") == "PNG"
    assert format_to_encoding("Jpeg") == "JPEG"


# --- make_crs ---


def test_make_crs_from_string():
    crs = make_crs("EPSG:4326")
    assert crs == CRS.from_epsg(4326)


def test_make_crs_from_int():
    crs = make_crs(4326)
    assert crs == CRS.from_epsg(4326)


def test_make_crs_from_dict():
    crs = make_crs({"init": "EPSG:4326"})
    assert crs is not None
