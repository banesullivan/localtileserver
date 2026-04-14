"""Tests for localtileserver.web.routers.utils edge cases."""

from localtileserver.web.routers.utils import get_clean_filename_from_params, parse_style_params

# --- get_clean_filename_from_params ---


def test_get_clean_filename_from_params_none():
    result = get_clean_filename_from_params(None)
    assert result is not None


def test_get_clean_filename_from_params_empty():
    result = get_clean_filename_from_params("")
    assert result is not None


# --- parse_style_params ---


def test_parse_style_params_all_none():
    assert parse_style_params() == {}


def test_parse_style_params_single_index():
    result = parse_style_params(indexes="1")
    assert result == {"indexes": "1"}


def test_parse_style_params_multi_index():
    result = parse_style_params(indexes="1,2,3")
    assert result == {"indexes": ["1", "2", "3"]}


def test_parse_style_params_comma_vmin():
    result = parse_style_params(vmin="0.5,1.0")
    assert result == {"vmin": ["0.5", "1.0"]}


def test_parse_style_params_comma_vmax():
    result = parse_style_params(vmax="100,200")
    assert result == {"vmax": ["100", "200"]}


def test_parse_style_params_comma_nodata():
    result = parse_style_params(nodata="-999,0")
    assert result == {"nodata": ["-999", "0"]}


def test_parse_style_params_indexes_attribute_error():
    # An int has no .split() method, so the except (ValueError, AttributeError)
    # branch catches it and passes through the raw value.
    result = parse_style_params(indexes=123)
    assert result == {"indexes": 123}


def test_parse_style_params_single_values():
    result = parse_style_params(vmin="10", vmax="200", nodata="0")
    assert result == {"vmin": "10", "vmax": "200", "nodata": "0"}
