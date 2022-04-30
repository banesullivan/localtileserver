import pytest

from localtileserver import get_leaflet_roi_controls, get_leaflet_tile_layer
from localtileserver.client import DEMO_REMOTE_TILE_SERVER, RemoteTileClient

skip_leaflet = False
try:
    from ipyleaflet import DrawControl, TileLayer, WidgetControl
except ImportError:
    skip_leaflet = True


@pytest.mark.skipif(skip_leaflet, reason="ipyleaflet not installed")
def test_leaflet_tile_layer(bahamas):
    layer = get_leaflet_tile_layer(bahamas)
    assert isinstance(layer, TileLayer)
    with pytest.raises(ValueError):
        layer = get_leaflet_tile_layer(bahamas, band=1, palette="foobar")
    layer = get_leaflet_tile_layer(
        bahamas, band=1, palette="matplotlib.Viridis_20", vmin=0, vmax=255, nodata=0
    )
    assert isinstance(layer, TileLayer)


@pytest.mark.skipif(skip_leaflet, reason="ipyleaflet not installed")
def test_leaflet_tile_layer_from_path(bahamas_file):
    layer = get_leaflet_tile_layer(bahamas_file)
    assert isinstance(layer, TileLayer)


@pytest.mark.skipif(skip_leaflet, reason="ipyleaflet not installed")
def test_get_leaflet_roi_controls(bahamas):
    draw_control, button_control = get_leaflet_roi_controls(bahamas)
    assert isinstance(draw_control, DrawControl)
    assert isinstance(button_control, WidgetControl)


def test_leaflet_with_remote_client(remote_file_url):
    client = RemoteTileClient(remote_file_url, host=DEMO_REMOTE_TILE_SERVER)
    layer = get_leaflet_tile_layer(client)
    assert isinstance(layer, TileLayer)
