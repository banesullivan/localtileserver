import pytest
import requests

from tileserver import TileServer

TOLERANCE = 2e-2


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


def test_server_shutdown(bahamas_tile_server):
    tile_url = bahamas_tile_server.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    bahamas_tile_server.shutdown()
    with pytest.raises(requests.ConnectionError):
        r = requests.get(tile_url)
        r.raise_for_status()


def test_server_delete(bahamas_tile_server):
    tile_url = bahamas_tile_server.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    bahamas_tile_server.__del__()  # Using `del` does not always work
    with pytest.raises(requests.ConnectionError):
        r = requests.get(tile_url)
        r.raise_for_status()
