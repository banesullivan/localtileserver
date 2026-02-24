"""Extended tests for localtileserver.client - targeting coverage gaps."""

from matplotlib.colors import LinearSegmentedColormap
import pytest
import rasterio
from rio_tiler.io import Reader

from localtileserver.client import TileClient, TilerInterface, get_or_create_tile_client
from localtileserver.examples import get_data_path


@pytest.fixture
def bahamas_path():
    return get_data_path("bahamas_rgb.tif")


@pytest.fixture
def tile_client(bahamas_path):
    client = TileClient(bahamas_path, debug=True)
    yield client
    client.shutdown(force=True)


# --- TilerInterface ---


def test_tiler_from_rasterio_dataset(bahamas_path):
    with rasterio.open(bahamas_path) as ds:
        ti = TilerInterface(ds)
        assert ti.filename == ds.name
        assert ti.dataset is not None


def test_tiler_from_reader(bahamas_path):
    reader = Reader(bahamas_path)
    ti = TilerInterface.__new__(TilerInterface)
    ti._reader = reader
    assert ti.reader is reader


def test_tiler_info_property(bahamas_path):
    ti = TilerInterface(bahamas_path)
    info = ti.info
    assert info is not None


def test_tiler_band_names(bahamas_path):
    ti = TilerInterface(bahamas_path)
    names = ti.band_names
    assert isinstance(names, list)
    assert len(names) == 3


def test_tiler_min_max_zoom(bahamas_path):
    ti = TilerInterface(bahamas_path)
    assert isinstance(ti.min_zoom, int)
    assert isinstance(ti.max_zoom, int)
    assert ti.min_zoom <= ti.max_zoom


def test_tiler_default_zoom(bahamas_path):
    ti = TilerInterface(bahamas_path)
    assert ti.default_zoom == ti.min_zoom


def test_tiler_thumbnail_with_crs(bahamas_path):
    ti = TilerInterface(bahamas_path)
    # Use EPSG:4326 which is the source CRS, avoiding reprojection issues
    thumb = ti.thumbnail(crs="EPSG:4326")
    assert len(thumb) > 0


def test_tiler_repr_png(bahamas_path):
    ti = TilerInterface(bahamas_path)
    png = ti._repr_png_()
    assert len(png) > 0


# --- TileServerMixin ---


def test_server_properties(tile_client):
    assert tile_client.server_port > 0
    assert tile_client.server_host == "127.0.0.1"
    assert "http://" in tile_client.server_base_url


def test_client_base_url_defaults(tile_client):
    url = tile_client.client_base_url
    assert isinstance(url, str)


def test_client_base_url_with_host(tile_client):
    tile_client.client_host = "example.com"
    tile_client.client_port = None
    url = tile_client.client_base_url
    assert "example.com" in url


def test_client_base_url_with_host_and_port(tile_client):
    tile_client.client_host = "example.com"
    tile_client.client_port = 8080
    url = tile_client.client_base_url
    assert "example.com:8080" in url


def test_client_base_url_with_port_only(tile_client):
    tile_client.client_host = None
    tile_client.client_port = 9999
    url = tile_client.client_base_url
    assert "9999" in url


def test_client_base_url_with_prefix(tile_client):
    tile_client.client_host = "example.com"
    tile_client.client_port = None
    tile_client.client_prefix = "/proxy/{port}"
    url = tile_client.client_base_url
    assert "/proxy/" in url


def test_client_base_url_relative(tile_client):
    tile_client.client_host = None
    tile_client.client_port = None
    tile_client.client_prefix = None
    url = tile_client.client_base_url
    assert url == "/"


def test_client_port_true(tile_client):
    tile_client.client_port = True
    assert tile_client.client_port == tile_client.server_port


def test_create_url_server(tile_client):
    url = tile_client.create_url("api/metadata", client=False)
    assert tile_client.server_base_url in url
    assert "filename=" in url


def test_create_url_client(tile_client):
    tile_client.client_host = "proxy.example.com"
    url = tile_client.create_url("api/metadata", client=True)
    assert "proxy.example.com" in url


def test_enable_colab(tile_client):
    tile_client.enable_colab()
    assert tile_client.client_host == "localhost"
    assert tile_client.client_port == tile_client.server_port


def test_get_tile_url(tile_client):
    url = tile_client.get_tile_url()
    assert "{z}" in url
    assert "{x}" in url
    assert "{y}" in url


def test_get_tile_url_with_params(tile_client):
    url = tile_client.get_tile_url(
        indexes=[1, 2, 3],
        colormap=None,
        vmin=0.0,
        vmax=255.0,
        nodata=0,
    )
    assert "vmin" in url
    assert "vmax" in url
    assert "nodata" in url


def test_get_tile_url_with_colormap(tile_client):
    url = tile_client.get_tile_url(colormap="viridis")
    assert "viridis" in url


def test_get_tile_url_custom_colormap(tile_client):
    cmap = LinearSegmentedColormap.from_list("test", ["red", "blue"], N=256)
    url = tile_client.get_tile_url(colormap=cmap)
    # Should use custom:hash instead of bloated JSON
    assert "custom%3A" in url or "custom:" in url
    assert len(url) < 2000  # Should not overflow


def test_get_tile_url_list_colormap(tile_client):
    url = tile_client.get_tile_url(colormap=["red", "green", "blue"])
    assert "colormap" in url


def test_get_tile_url_vmin_iterable_without_indexes_raises(tile_client):
    with pytest.raises(ValueError, match="indexes"):
        tile_client.get_tile_url(vmin=[0.0, 0.0])


def test_get_tile_url_vmax_iterable_without_indexes_raises(tile_client):
    with pytest.raises(ValueError, match="indexes"):
        tile_client.get_tile_url(vmax=[255.0, 255.0])


def test_get_tile_url_nodata_iterable_without_indexes_raises(tile_client):
    with pytest.raises(ValueError, match="indexes"):
        tile_client.get_tile_url(nodata=[0, 0])


def test_shutdown(bahamas_path):
    client = TileClient(bahamas_path, debug=True)
    client.shutdown(force=True)


def test_client_with_http_host(tile_client):
    tile_client.client_host = "https://secure.example.com"
    url = tile_client.client_base_url
    # Should not double up the scheme
    assert url.startswith("https://secure.example.com")
    assert not url.startswith("http://https://")


# --- get_or_create_tile_client ---


def test_get_or_create_from_path(bahamas_path):
    client, created = get_or_create_tile_client(bahamas_path, debug=True)
    assert created is True
    assert isinstance(client, TileClient)
    client.shutdown(force=True)


def test_get_or_create_from_existing_client(tile_client):
    client, created = get_or_create_tile_client(tile_client)
    assert created is False
    assert client is tile_client
