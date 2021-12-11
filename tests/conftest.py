from osgeo import gdal
import pytest

from localtileserver.examples import get_bahamas, get_blue_marble, get_data_path
from localtileserver.tileserver import create_app


@pytest.fixture
def flask_client():
    app = create_app()
    with app.test_client() as client:
        yield client


@pytest.fixture
def bahamas_file():
    return get_data_path("bahamas_rgb.tif")


@pytest.fixture
def bahamas(port="default", debug=True):
    # Using debug True since in a testing environment
    tile_client = get_bahamas(port=port, debug=debug)
    yield tile_client
    tile_client.shutdown(force=True)


@pytest.fixture
def blue_marble(port="default", debug=True):
    # Using debug True since in a testing environment
    tile_client = get_blue_marble(port=port, debug=debug)
    yield tile_client
    tile_client.shutdown(force=True)


@pytest.fixture
def remote_file_url():
    return "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif"


@pytest.fixture
def remote_file_s3():
    gdal.SetConfigOption("AWS_NO_SIGN_REQUEST", "YES")
    return "s3://sentinel-cogs/sentinel-s2-l2a-cogs/2020/S2A_31QHU_20200714_0_L2A/B01.tif"
