import pytest
import requests

from localtileserver.client import (
    DEMO_REMOTE_TILE_SERVER,
    RemoteTileClient,
    get_or_create_tile_client,
)


@pytest.mark.xfail
def test_remote_client(remote_file_url):
    tile_client = RemoteTileClient(remote_file_url, host=DEMO_REMOTE_TILE_SERVER)
    assert tile_client.metadata()
    url = tile_client.get_tile_url(projection=None).format(z=0, x=0, y=0)
    r = requests.get(url)
    r.raise_for_status()
    assert r.content


def test_get_or_create_tile_client(remote_file_url):
    tile_client = RemoteTileClient(remote_file_url, host=DEMO_REMOTE_TILE_SERVER)
    same, created = get_or_create_tile_client(tile_client)
    assert not created
    assert tile_client == same
