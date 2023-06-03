import os
import platform

import pytest
import rasterio
import requests
from server_thread import ServerDownError, ServerManager

from localtileserver.client import RestTileClient
from localtileserver.tiler import get_clean_filename, get_tile_bounds, get_tile_source
from localtileserver.utilities import ImageBytes

skip_shapely = False
try:
    from shapely.geometry import box
except ImportError:
    skip_shapely = True

skip_mac_arm = pytest.mark.skipif(
    platform.system() == "Darwin" and platform.processor() == "arm", reason="MacOS Arm issues."
)

TOLERANCE = 2e-2


def get_content(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.content


def test_create_tile_client(bahamas_file):
    assert ServerManager.server_count() == 0
    tile_client = RestTileClient(bahamas_file, debug=True)
    assert tile_client.filename == get_clean_filename(bahamas_file)
    assert tile_client.server_port
    assert tile_client.server_base_url
    assert "bounds" in tile_client.metadata()
    assert tile_client.bounds()
    center = tile_client.center()
    assert center[0] == pytest.approx(24.5579, abs=TOLERANCE)
    assert center[1] == pytest.approx(-77.7668, abs=TOLERANCE)
    tile_url = tile_client.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    tile_conent = tile_client.get_tile(z=8, x=72, y=110)
    assert tile_conent
    tile_url = tile_client.get_tile_url(grid=True).format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    tile_url = tile_client.create_url("api/tiles/debug/{z}/{x}/{y}.png".format(z=8, x=72, y=110))
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    tile_url = tile_client.get_tile_url(palette="matplotlib.Plasma_6").format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    thumb = tile_client.thumbnail()
    assert isinstance(thumb, ImageBytes)
    assert thumb.mimetype == "image/png"
    tile_client.shutdown(force=True)


def test_create_tile_client_bad(bahamas_file):
    with pytest.raises(OSError):
        RestTileClient("foo.tif", debug=True)
    with pytest.raises(ValueError):
        RestTileClient(bahamas_file, port="0", debug=True)


def test_client_force_shutdown(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    tile_url = bahamas.get_tile_url().format(z=8, x=72, y=110)
    r = requests.get(tile_url)
    r.raise_for_status()
    assert r.content
    assert ServerManager.server_count() == 1
    bahamas.shutdown(force=True)
    assert ServerManager.server_count() == 0
    with pytest.raises(requests.ConnectionError):
        r = requests.get(tile_url)
        r.raise_for_status()
    with pytest.raises(ServerDownError):
        bahamas.bounds()


# def test_multiple_tile_clients_one_server(bahamas_file, blue_marble):
#     assert ServerManager.server_count() == 1
#     tile_url_a = bahamas.get_tile_url().format(z=8, x=72, y=110)
#     tile_url_b = blue_marble.get_tile_url().format(z=8, x=72, y=110)
#     assert get_content(tile_url_a) != get_content(tile_url_b)
#     thumb_url_a = bahamas.create_url("api/thumbnail.png")
#     thumb_url_b = blue_marble.create_url("api/thumbnail.png")
#     assert get_content(thumb_url_a) != get_content(thumb_url_b)


def test_extract_roi_world(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    # -78.047, -77.381, 24.056, 24.691
    path = bahamas.extract_roi(-78.047, -77.381, 24.056, 24.691, return_path=True)
    assert path.exists()
    source = get_tile_source(path, projection="EPSG:3857")
    assert source.getMetadata()["geospatial"]
    e = get_tile_bounds(source, projection="EPSG:4326")
    assert e["xmin"] == pytest.approx(-78.047, abs=TOLERANCE)
    assert e["xmax"] == pytest.approx(-77.381, abs=TOLERANCE)
    assert e["ymin"] == pytest.approx(24.056, abs=TOLERANCE)
    assert e["ymax"] == pytest.approx(24.691, abs=TOLERANCE)
    roi = bahamas.extract_roi(-78.047, -77.381, 24.056, 24.691, return_bytes=True)
    assert isinstance(roi, ImageBytes)
    assert roi.mimetype == "image/tiff"
    roi = bahamas.extract_roi(-78.047, -77.381, 24.056, 24.691)
    assert roi.metadata()["geospatial"]


@pytest.mark.skipif(skip_shapely, reason="shapely not installed")
def test_extract_roi_world_shape(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    poly = box(-78.047, 24.056, -77.381, 24.691)
    path = bahamas.extract_roi_shape(poly, return_path=True)
    assert path.exists()
    source = get_tile_source(path, projection="EPSG:3857")
    assert source.getMetadata()["geospatial"]
    e = get_tile_bounds(source, projection="EPSG:4326")
    assert e["xmin"] == pytest.approx(-78.047, abs=TOLERANCE)
    assert e["xmax"] == pytest.approx(-77.381, abs=TOLERANCE)
    assert e["ymin"] == pytest.approx(24.056, abs=TOLERANCE)
    assert e["ymax"] == pytest.approx(24.691, abs=TOLERANCE)
    path = bahamas.extract_roi_shape(poly.wkt, return_path=True)
    assert path.exists()


@pytest.mark.skip
def test_extract_roi_pixel(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    path = bahamas.extract_roi_pixel(100, 500, 300, 600, return_path=True)
    assert path.exists()
    source = get_tile_source(path)
    assert source.getMetadata()["geospatial"]
    assert source.getMetadata()["sizeX"] == 400
    assert source.getMetadata()["sizeY"] == 300
    roi = bahamas.extract_roi_pixel(100, 500, 300, 600)
    assert roi.metadata()["geospatial"]
    roi = bahamas.extract_roi_pixel(100, 500, 300, 600, return_bytes=True)
    assert isinstance(roi, ImageBytes)


def test_caching_query_params(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    thumb_url_a = bahamas.create_url("api/thumbnail.png")
    thumb_url_b = bahamas.create_url("api/thumbnail.png?band=1")
    assert get_content(thumb_url_a) != get_content(thumb_url_b)
    thumb_url_c = bahamas.create_url("api/thumbnail.png")
    assert get_content(thumb_url_a) == get_content(thumb_url_c)


def test_multiband(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
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


def test_multiband_vmin_vmax(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    # Check that other options are well handled
    url = bahamas.get_tile_url(
        band=[3, 2, 1],
        vmax=[100, 200, 250],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    url = bahamas.get_tile_url(
        band=[3, 2, 1],
        vmin=[0, 10, 50],
        vmax=[100, 200, 250],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    with pytest.raises(ValueError):
        bahamas.get_tile_url(
            vmax=[100, 200, 250],
        ).format(z=8, x=72, y=110)


def test_launch_non_default_server(bahamas_file):
    default = RestTileClient(bahamas_file)
    diff = RestTileClient(bahamas_file, port=0)
    assert default.server != diff.server
    assert default.server_port != diff.server_port


def test_pixel(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    # pix = bahamas.pixel(0, 0)  # pixel space
    # assert "bands" in pix
    pix = bahamas.pixel(24.56, -77.76, units="EPSG:4326")  # world coordinates
    assert "bands" in pix


@pytest.mark.skip
def test_histogram(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    hist = bahamas.histogram()
    assert len(hist)


@pytest.mark.parametrize("encoding", ["PNG", "JPEG", "JPG"])
def test_thumbnail_encodings(bahamas_file, encoding):
    bahamas = RestTileClient(bahamas_file)
    # large-image's rasterio source cannot handle: "TIF", "TIFF"
    thumbnail = bahamas.thumbnail(encoding=encoding)
    assert thumbnail  # TODO: check content
    assert isinstance(thumbnail, ImageBytes)
    thumbnail = bahamas.thumbnail(encoding=encoding, output_path=True)
    assert os.path.exists(thumbnail)


def test_thumbnail_bad_encoding(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    with pytest.raises(ValueError):
        bahamas.thumbnail(encoding="foo")


def test_custom_palette(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    palette = ["#006633", "#E5FFCC", "#662A00", "#D8D8D8", "#F5F5F5"]
    thumbnail = bahamas.thumbnail(
        band=1,
        palette=palette,
        scheme="discrete",
    )
    assert thumbnail  # TODO: check colors in produced image
    thumbnail = bahamas.thumbnail(
        band=1,
        cmap=palette,
        scheme="linear",
    )
    assert thumbnail  # TODO: check colors in produced image


def test_style_dict(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    style = {
        "bands": [
            {"band": 1, "palette": ["#000", "#0f0"]},
        ]
    }
    thumbnail = bahamas.thumbnail(
        style=style,
    )
    assert thumbnail  # TODO: check colors in produced image


def test_rasterio_property(bahamas_file):
    bahamas = RestTileClient(bahamas_file)
    src = bahamas.rasterio
    assert isinstance(src, rasterio.io.DatasetReaderBase)
    assert src == bahamas.rasterio
