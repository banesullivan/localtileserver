from localtileserver.server import TileClient


def test_tileclient_with_vsi(remote_file_url):
    tile_client = TileClient(remote_file_url)
    assert "bounds" in tile_client.metadata()
