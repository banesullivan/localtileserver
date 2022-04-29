import pytest

from localtileserver.client import TileClient


def test_tileclient_with_vsi(remote_file_url):
    client = TileClient(remote_file_url)
    assert "bounds" in client.metadata()


@pytest.mark.skip
def test_tileclient_with_vsi_s3(remote_file_s3):
    client = TileClient(remote_file_s3)
    assert "bounds" in client.metadata()
