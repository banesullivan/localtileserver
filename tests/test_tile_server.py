import pytest
import requests

from tileserver.server import _LIVE_SERVERS, TileServerThread


def test_server_force_shutdown(bahamas):
    tile_url = bahamas.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    assert len(_LIVE_SERVERS) == 1
    bahamas.shutdown(force=True)
    assert len(_LIVE_SERVERS) == 0
    with pytest.raises(requests.ConnectionError):
        r = requests.get(tile_url)
        r.raise_for_status()
    with pytest.raises(TileServerThread.ServerDownError):
        bahamas.bounds()
