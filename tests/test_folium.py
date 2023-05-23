import pytest

from localtileserver import LocalTileServerLayerMixin, get_folium_tile_layer
from localtileserver.client import DEMO_REMOTE_TILE_SERVER, RemoteTileClient

skip_folium = False
try:
    from folium import TileLayer
except ImportError:
    skip_folium = True


@pytest.mark.skipif(skip_folium, reason="folium not installed")
def test_leaflet_tile_layer(bahamas):
    layer = get_folium_tile_layer(bahamas)
    assert isinstance(layer, TileLayer)
    with pytest.raises(ValueError):
        layer = get_folium_tile_layer(bahamas, band=1, palette="foobar")
    layer = get_folium_tile_layer(
        bahamas, band=1, palette="matplotlib.Viridis_20", vmin=0, vmax=255, nodata=0
    )
    assert isinstance(layer, TileLayer)
    assert isinstance(layer, LocalTileServerLayerMixin)


@pytest.mark.skipif(skip_folium, reason="folium not installed")
def test_folium_tile_layer_from_path(bahamas_file):
    layer = get_folium_tile_layer(bahamas_file)
    assert isinstance(layer, TileLayer)
    assert isinstance(layer, LocalTileServerLayerMixin)


@pytest.mark.xfail
@pytest.mark.skipif(skip_folium, reason="folium not installed")
def test_folium_with_remote_client(remote_file_url):
    client = RemoteTileClient(remote_file_url, host=DEMO_REMOTE_TILE_SERVER)
    layer = get_folium_tile_layer(client)
    assert isinstance(layer, TileLayer)
