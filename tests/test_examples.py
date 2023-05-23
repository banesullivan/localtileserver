import pytest

from localtileserver import examples

skip_shapely = False
try:
    import shapely  # noqa
except ImportError:
    skip_shapely = True


def test_get_blue_marble():
    client = examples.get_blue_marble()
    assert client.metadata()


def test_get_virtual_earth():
    client = examples.get_virtual_earth()
    assert client.metadata()


def test_get_arcgis():
    client = examples.get_arcgis()
    assert client.metadata()


def test_get_elevation():
    client = examples.get_elevation()
    assert client.metadata()


def test_get_bahamas():
    client = examples.get_bahamas()
    assert client.metadata()


def test_get_pine_gulch():
    client = examples.get_pine_gulch()
    assert client.metadata()


def test_get_landsat():
    client = examples.get_landsat()
    assert client.metadata()


def test_get_san_francisco():
    client = examples.get_san_francisco()
    assert client.metadata()


def test_get_oam2():
    client = examples.get_oam2()
    assert client.metadata()


def test_get_elevation_us():
    client = examples.get_elevation_us()
    assert client.metadata()


@pytest.mark.xfail(reason="Flaky HTTP request failures")
def test_get_co_elevation():
    client = examples.get_co_elevation()
    assert client.metadata()


def test_get_co_elevation_roi():
    client = examples.get_co_elevation(local_roi=True)
    assert client.metadata()


@pytest.mark.skipif(skip_shapely, reason="shapely not installed")
def test_load_presidio():
    presidio = examples.load_presidio()
    assert presidio
