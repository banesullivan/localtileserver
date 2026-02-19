import shutil
import subprocess

import pytest

from localtileserver.tiler import get_clean_filename
from localtileserver.tiler.data import get_data_path

has_gdaltindex = shutil.which("gdaltindex") is not None
has_gti_driver = False
try:
    from osgeo import gdal

    has_gti_driver = gdal.GetDriverByName("GTI") is not None
except ImportError:
    pass

requires_gti = pytest.mark.skipif(
    not (has_gdaltindex and has_gti_driver),
    reason="Requires gdaltindex CLI and GDAL GTI driver (GDAL >= 3.9)",
)


# --- Unit tests for GDAL driver prefix handling in get_clean_filename ---


@pytest.mark.parametrize(
    "prefix",
    ["GTI:", "WMTS:", "DAAS:", "EEDAI:", "NGW:", "PLMOSAIC:", "PLSCENES:"],
)
def test_gdal_prefix_passthrough(prefix):
    """GDAL driver prefixes should be returned as-is without path manipulation."""
    path = f"{prefix}/some/path/to/file.gpkg"
    result = get_clean_filename(path)
    assert result == path


def test_gti_prefix_with_absolute_path():
    result = get_clean_filename("GTI:/usr/local/data/index.gpkg")
    assert result == "GTI:/usr/local/data/index.gpkg"


def test_gti_prefix_preserves_case():
    result = get_clean_filename("GTI:/path/to/file.gpkg")
    assert result.startswith("GTI:")


def test_regular_path_not_affected(tmp_path):
    """Normal file paths should still go through standard resolution."""
    test_file = tmp_path / "test.tif"
    test_file.write_bytes(b"fake")
    result = get_clean_filename(str(test_file))
    assert str(result) == str(test_file)


def test_http_url_not_affected():
    """HTTP URLs should still produce /vsicurl paths."""
    result = get_clean_filename("https://example.com/test.tif")
    assert "/vsicurl" in str(result)


def test_s3_url_not_affected():
    """S3 URLs should still produce /vsis3 paths."""
    result = get_clean_filename("s3://bucket/key.tif")
    assert "/vsis3" in str(result)


def test_vsi_path_not_affected():
    """VSI paths should still be returned as-is."""
    result = get_clean_filename("/vsicurl/https://example.com/test.tif")
    assert result == "/vsicurl/https://example.com/test.tif"


def test_invalid_path_still_raises():
    """Non-existent local paths should still raise OSError."""
    with pytest.raises(OSError):
        get_clean_filename("/nonexistent/path/file.tif")


# --- Integration tests requiring GDAL GTI driver ---


@pytest.fixture
def gti_index(tmp_path):
    """Create a GTI index from the bundled bahamas sample raster."""
    source_tif = get_data_path("bahamas_rgb.tif")
    index_path = tmp_path / "test_index.gti.gpkg"
    result = subprocess.run(
        ["gdaltindex", "-f", "GPKG", str(index_path), str(source_tif)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"gdaltindex failed: {result.stderr}"
    return str(index_path)


@requires_gti
def test_get_clean_filename_gti_prefix(gti_index):
    """get_clean_filename should pass GTI: prefixed paths through."""
    gti_path = f"GTI:{gti_index}"
    result = get_clean_filename(gti_path)
    assert result == gti_path


@requires_gti
def test_get_clean_filename_gti_extension(gti_index):
    """get_clean_filename should accept .gti.gpkg files as regular paths."""
    result = get_clean_filename(gti_index)
    assert str(result) == gti_index


@requires_gti
def test_tileclient_gti_prefix(gti_index):
    from localtileserver import TileClient

    client = TileClient(f"GTI:{gti_index}", debug=True)
    try:
        bounds = client.bounds()
        assert bounds is not None
        assert len(bounds) == 4
    finally:
        client.shutdown(force=True)


@requires_gti
def test_tileclient_gti_extension(gti_index):
    from localtileserver import TileClient

    client = TileClient(gti_index, debug=True)
    try:
        bounds = client.bounds()
        assert bounds is not None
        assert len(bounds) == 4
    finally:
        client.shutdown(force=True)


@requires_gti
def test_tileclient_gti_thumbnail(gti_index):
    from localtileserver import TileClient

    client = TileClient(f"GTI:{gti_index}", debug=True)
    try:
        thumb = client.thumbnail()
        assert thumb is not None
        assert len(thumb) > 0
    finally:
        client.shutdown(force=True)
