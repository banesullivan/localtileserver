import pytest
import requests

from localtileserver.server import _LIVE_SERVERS, TileClient, TileServerThread
from localtileserver.utilities import get_tile_source

TOLERANCE = 2e-2


def get_content(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.content


def test_create_tile_client(bahamas_file):
    tile_client = TileClient(bahamas_file, debug=True)
    assert tile_client.filename == bahamas_file
    assert tile_client.port
    assert tile_client.base_url
    assert "bounds" in tile_client.metadata()
    assert tile_client.bounds()
    center = tile_client.center()
    assert center[0] == pytest.approx(24.5579, abs=TOLERANCE)
    assert center[1] == pytest.approx(-77.7668, abs=TOLERANCE)
    tile_url = tile_client.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    tile_url = tile_client.get_tile_url(palette="matplotlib.Plasma_6").format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content


def test_create_tile_client_bad_filename():
    with pytest.raises(OSError):
        TileClient("foo.tif", debug=True)


def test_client_force_shutdown(bahamas):
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


def test_multiple_tile_clients_one_server(bahamas, blue_marble):
    assert len(_LIVE_SERVERS) == 1
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
    path = bahamas.extract_roi_pixel(100, 500, 300, 600, encoding="PNG")
    assert path.exists()
    source = get_tile_source(path)
    assert "geospatial" not in source.getMetadata()


def test_caching_query_params(bahamas):
    thumb_url_a = bahamas.create_url("thumbnail")
    thumb_url_b = bahamas.create_url("thumbnail?band=1")
    assert get_content(thumb_url_a) != get_content(thumb_url_b)


def test_multiband(bahamas):
    # Create an RGB tile in several ways and make sure all same
    url_a = bahamas.get_tile_url(
        band=[1, 2, 3],
    ).format(z=8, x=72, y=110)
    url_b = bahamas.get_tile_url(
        band=[3, 2, 1],
        palette=["b", "g", "r"],
    ).format(z=8, x=72, y=110)
    url_c = bahamas.get_tile_url().format(z=8, x=72, y=110)
    assert get_content(url_a) == get_content(url_b) == get_content(url_c)
    # Check that other options are well handled
    url = bahamas.get_tile_url(
        band=[1, 2, 3],
        palette=["b", "g", "r"],
        vmin=0,
        vmax=300,
        nodata=0,
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
