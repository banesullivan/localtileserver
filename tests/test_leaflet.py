import pytest

from tileserver import get_leaflet_tile_layer

skip_leaflet = False
try:
    from ipyleaflet import TileLayer
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
