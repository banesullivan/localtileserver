import pytest

from localtileserver import LocalTileServerLayerMixin, get_leaflet_tile_layer

skip_leaflet = False
try:
    from ipyleaflet import TileLayer
except ImportError:
    skip_leaflet = True

skip_shapely = False
try:
    import shapely  # noqa
except ImportError:
    skip_shapely = True


@pytest.mark.skipif(skip_leaflet, reason="ipyleaflet not installed")
def test_leaflet_tile_layer(bahamas):
    layer = get_leaflet_tile_layer(bahamas)
    assert isinstance(layer, TileLayer)
    with pytest.raises(ValueError):
        layer = get_leaflet_tile_layer(bahamas, indexes=1, colormap="foobar")
    layer = get_leaflet_tile_layer(
        bahamas, indexes=1, colormap="viridis", vmin=0, vmax=255, nodata=0
    )
    assert isinstance(layer, TileLayer)
    assert isinstance(layer, LocalTileServerLayerMixin)


@pytest.mark.skipif(skip_leaflet, reason="ipyleaflet not installed")
def test_leaflet_tile_layer_from_path(bahamas_file):
    layer = get_leaflet_tile_layer(bahamas_file)
    assert isinstance(layer, TileLayer)
    assert isinstance(layer, LocalTileServerLayerMixin)


@pytest.mark.skipif(skip_leaflet, reason="ipyleaflet not installed")
@pytest.mark.parametrize("stretch", ["linear", "minmax", "equalize"])
def test_leaflet_tile_layer_stretch(bahamas, stretch):
    layer = get_leaflet_tile_layer(bahamas, indexes=1, colormap="viridis", stretch=stretch)
    assert isinstance(layer, TileLayer)
    assert f"stretch={stretch}" in layer.url
