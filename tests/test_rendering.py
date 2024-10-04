from matplotlib.colors import ListedColormap
import pytest

from .utilities import get_content


def test_thumbnail(bahamas, compare):
    thumb_a = bahamas.thumbnail()
    thumb_b = bahamas.thumbnail(
        indexes=[1, 2, 3],
    )
    assert thumb_a == thumb_b
    compare(thumb_a)


@pytest.mark.parametrize("colormap,indexes", [("viridis", None), ("viridis", 1), ("inferno", 1)])
def test_thumbnail_colormap(bahamas, compare, colormap, indexes):
    thumb = bahamas.thumbnail(colormap=colormap, indexes=indexes)
    compare(thumb)


def test_tile(
    bahamas,
    compare,
):
    url_a = bahamas.get_tile_url().format(z=8, x=72, y=110)
    tile_a = get_content(url_a)
    url_b = bahamas.get_tile_url(
        indexes=[1, 2, 3],
    ).format(z=8, x=72, y=110)
    tile_b = get_content(url_b)
    direct_content = bahamas.tile(z=8, x=72, y=110, indexes=[1, 2, 3])
    assert tile_a == tile_b == direct_content
    compare(direct_content)


@pytest.mark.parametrize("indexes", [[3, 2, 1], [2, 1, 3], 1, 2, 3])
def test_tile_indexes(bahamas, compare, indexes):
    url_a = bahamas.get_tile_url(indexes=indexes).format(z=8, x=72, y=110)
    tile_a = get_content(url_a)
    direct_content = bahamas.tile(z=8, x=72, y=110, indexes=indexes)
    assert tile_a == direct_content
    compare(direct_content)


@pytest.mark.parametrize(
    "colormap,indexes", [(None, None), ("viridis", None), ("viridis", 1), ("inferno", 1)]
)
def test_tile_colormap(bahamas, compare, colormap, indexes):
    # Get a tile over the REST API
    tile_url = bahamas.get_tile_url(colormap=colormap, indexes=indexes).format(z=8, x=72, y=110)
    rest_content = get_content(tile_url)
    # Get tile directly
    direct_content = bahamas.tile(z=8, x=72, y=110, colormap=colormap, indexes=indexes)
    # Make sure they are the same
    assert rest_content == direct_content
    compare(direct_content)


@pytest.mark.parametrize(
    "colormap,indexes",
    [
        (ListedColormap(["red", "blue"]), None),
        (ListedColormap(["blue", "green"]), 2),
    ],
)
def test_custom_colormap(bahamas, compare, colormap, indexes):
    # Get a tile over the REST API
    tile_url = bahamas.get_tile_url(colormap=colormap, indexes=indexes).format(z=8, x=72, y=110)
    rest_content = get_content(tile_url)
    # Get tile directly
    direct_content = bahamas.tile(z=8, x=72, y=110, colormap=colormap, indexes=indexes)
    # Make sure they are the same
    assert rest_content == direct_content
    compare(direct_content)


@pytest.mark.parametrize("vmin", [100, [100, 200, 250]])
def test_tile_vmin(bahamas, compare, vmin):
    url = bahamas.get_tile_url(
        indexes=[1, 2, 3],
        vmin=vmin,
    ).format(z=8, x=72, y=110)
    tile_a = get_content(url)
    direct_content = bahamas.tile(z=8, x=72, y=110, indexes=[1, 2, 3], vmin=vmin)
    assert tile_a == direct_content
    compare(direct_content)


@pytest.mark.parametrize("vmax", [100, [100, 200, 250]])
def test_tile_vmax(bahamas, compare, vmax):
    url = bahamas.get_tile_url(
        indexes=[1, 2, 3],
        vmax=vmax,
    ).format(z=8, x=72, y=110)
    tile_a = get_content(url)
    direct_content = bahamas.tile(z=8, x=72, y=110, indexes=[1, 2, 3], vmax=vmax)
    assert tile_a == direct_content
    compare(direct_content)


@pytest.mark.parametrize("nodata", [None, 0, 255])
def test_thumbnail_nodata(bahamas, compare, nodata):
    thumb = bahamas.thumbnail(nodata=nodata)
    compare(thumb)


@pytest.mark.parametrize("nodata", [None, 0, 255])
def test_tile_nodata(bahamas, compare, nodata):
    url = bahamas.get_tile_url(
        nodata=nodata,
    ).format(z=8, x=72, y=110)
    tile_a = get_content(url)
    direct_content = bahamas.tile(z=8, x=72, y=110, nodata=nodata)
    assert tile_a == direct_content
    compare(direct_content)


def test_tile_vmin_vmax(bahamas, compare):
    url = bahamas.get_tile_url(vmin=50, vmax=100).format(z=8, x=72, y=110)
    tile_a = get_content(url)
    direct_content = bahamas.tile(z=8, x=72, y=110, vmin=50, vmax=100)
    assert tile_a == direct_content
    compare(direct_content)


@pytest.mark.parametrize("nodata", [None, 0, 255])
def test_landsat7_nodata(landsat7, compare, nodata):
    thumbnail = landsat7.thumbnail(nodata=nodata)
    compare(thumbnail)
