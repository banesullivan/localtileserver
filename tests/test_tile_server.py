import pytest
import requests

from tileserver import TileServer
from tileserver.application.paths import _THREAD_FILE_PATHS
from tileserver.utilities import get_tile_source

TOLERANCE = 2e-2


def get_content(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.content


def test_create_tile_server(bahamas_file):
    tile_server = TileServer(bahamas_file, debug=True)
    assert tile_server.path == bahamas_file
    assert tile_server.port
    assert tile_server.base_url
    assert "bounds" in tile_server.metadata()
    assert tile_server.bounds()
    center = tile_server.center()
    assert center[0] == pytest.approx(24.5579, abs=TOLERANCE)
    assert center[1] == pytest.approx(-77.7668, abs=TOLERANCE)
    tile_url = tile_server.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content


def test_server_shutdown(bahamas):
    tile_url = bahamas.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    assert len(_THREAD_FILE_PATHS) == 1
    bahamas.shutdown()
    assert len(_THREAD_FILE_PATHS) == 0
    with pytest.raises(requests.ConnectionError):
        r = requests.get(tile_url)
        r.raise_for_status()


def test_server_delete(bahamas):
    tile_url = bahamas.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    assert len(_THREAD_FILE_PATHS) == 1
    bahamas.__del__()  # Using `del` does not always work
    assert len(_THREAD_FILE_PATHS) == 0
    with pytest.raises(requests.ConnectionError):
        r = requests.get(tile_url)
        r.raise_for_status()


def test_multiple_tile_servers(bahamas, blue_marble):
    assert bahamas.port != blue_marble.port
    tile_url_a = bahamas.get_tile_url().format(z=8, x=72, y=110)
    tile_url_b = blue_marble.get_tile_url().format(z=8, x=72, y=110)
    assert get_content(tile_url_a) != get_content(tile_url_b)
    thumb_url_a = bahamas.create_url("thumbnail")
    thumb_url_b = blue_marble.create_url("thumbnail")
    assert get_content(thumb_url_a) != get_content(thumb_url_b)


def test_extract_roi_world(bahamas):
    # -78.047, -77.381, 24.056, 24.691
    path = bahamas.extract_roi(-78.047, -77.381, 24.056, 24.691)
    assert path.exists()
    source = get_tile_source(path)
    assert source.getMetadata()["geospatial"]


def test_extract_roi_pixel(bahamas):
    path = bahamas.extract_roi_pixel(100, 500, 300, 600)
    assert path.exists()
    source = get_tile_source(path)
    assert source.getMetadata()["geospatial"]


def test_caching_query_params(bahamas):
    thumb_url_a = bahamas.create_url("thumbnail")
    thumb_url_b = bahamas.create_url("thumbnail?band=1")
    assert get_content(thumb_url_a) != get_content(thumb_url_b)
