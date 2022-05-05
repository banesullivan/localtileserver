from osgeo import gdal
import pytest

from localtileserver.examples import get_bahamas, get_blue_marble, get_data_path, get_pelvis
from localtileserver.tileserver import create_app


@pytest.fixture
def flask_client():
    app = create_app()
    with app.test_client() as f_client:
        yield f_client


@pytest.fixture
def bahamas_file():
    return get_data_path("bahamas_rgb.tif")


@pytest.fixture
def bahamas(port="default", debug=True):
    # Using debug True since in a testing environment
    client = get_bahamas(port=port, debug=debug)
    yield client
    client.shutdown(force=True)


@pytest.fixture
def pelvis(port="default", debug=True):
    # Using debug True since in a testing environment
    client = get_pelvis(port=port, debug=debug)
    yield client
    client.shutdown(force=True)


@pytest.fixture
def blue_marble(port="default", debug=True):
    # Using debug True since in a testing environment
    client = get_blue_marble(port=port, debug=debug)
    yield client
    client.shutdown(force=True)


@pytest.fixture
def remote_file_url():
    return "https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif"


@pytest.fixture
def remote_file_s3():
    gdal.SetConfigOption("AWS_NO_SIGN_REQUEST", "YES")
    gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
    yield "s3://sentinel-cogs/sentinel-s2-l2a-cogs/2020/S2A_34JCL_20200309_0_L2A/B01.tif"
    gdal.SetConfigOption("GDAL_PAM_ENABLED", "YES")
