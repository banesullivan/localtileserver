"""Tests for localtileserver.utilities.save_file_from_request."""

from unittest.mock import MagicMock, patch

from localtileserver.utilities import save_file_from_request


def _make_response(filename="test.tif", content=b"fake raster data"):
    response = MagicMock()
    response.headers = {"content-disposition": f"attachment; filename={filename}"}
    response.content = content
    return response


def test_save_file_explicit_path(tmp_path):
    response = _make_response()
    out = tmp_path / "output.tif"
    result = save_file_from_request(response, out)
    assert result == out
    assert out.read_bytes() == b"fake raster data"


def test_save_file_false_path(tmp_path):
    response = _make_response()
    with patch("localtileserver.utilities.get_cache_dir", return_value=tmp_path):
        result = save_file_from_request(response, False)
    assert result == tmp_path / "test.tif"
    assert result.exists()
    assert result.read_bytes() == b"fake raster data"


def test_save_file_none_path(tmp_path):
    response = _make_response()
    with patch("localtileserver.utilities.get_cache_dir", return_value=tmp_path):
        result = save_file_from_request(response, None)
    assert result == tmp_path / "test.tif"
    assert result.exists()
    assert result.read_bytes() == b"fake raster data"
