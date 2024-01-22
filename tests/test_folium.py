import pytest

from localtileserver import LocalTileServerLayerMixin, get_folium_tile_layer

skip_folium = False
try:
    from folium import TileLayer
except ImportError:
    skip_folium = True


@pytest.mark.skipif(skip_folium, reason="folium not installed")
def test_folium_tile_layer(bahamas):
    layer = get_folium_tile_layer(bahamas)
    assert isinstance(layer, TileLayer)
    with pytest.raises(ValueError):
        layer = get_folium_tile_layer(bahamas, indexes=1, colormap="foobar")
    layer = get_folium_tile_layer(
        bahamas, indexes=1, colormap="viridis", vmin=0, vmax=255, nodata=0
    )
    assert isinstance(layer, TileLayer)
    assert isinstance(layer, LocalTileServerLayerMixin)


@pytest.mark.skipif(skip_folium, reason="folium not installed")
def test_folium_tile_layer_from_path(bahamas_file):
    layer = get_folium_tile_layer(bahamas_file)
    assert isinstance(layer, TileLayer)
    assert isinstance(layer, LocalTileServerLayerMixin)
