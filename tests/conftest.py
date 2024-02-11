from pathlib import Path

from matplotlib.testing.compare import compare_images
import pytest
import rasterio

from localtileserver.examples import get_bahamas, get_blue_marble, get_data_path, get_landsat7
from localtileserver.web import create_app


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
def landsat7(port="default", debug=True):
    # Using debug True since in a testing environment
    client = get_landsat7(port=port, debug=debug)
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
    return "https://github.com/giswqs/data/raw/main/raster/landsat7.tif"


@pytest.fixture
def remote_file_s3():
    with rasterio.Env(GDAL_PAM_ENABLED="NO", AWS_NO_SIGN_REQUEST="YES"):
        yield "s3://sentinel-cogs/sentinel-s2-l2a-cogs/2020/S2A_34JCL_20200309_0_L2A/B01.tif"


@pytest.fixture
def compare(request):
    calling_function_name = request.node.name

    def _compare(image: bytes):
        path = Path(__file__).parent / "baseline"
        gen = Path(__file__).parent / "generated"
        path.mkdir(exist_ok=True)
        gen.mkdir(exist_ok=True)
        filename = f"{calling_function_name}.png"
        if not (path / filename).exists():
            with open(path / filename, "wb") as f:
                f.write(image)
        else:
            with open(gen / filename, "wb") as f:
                f.write(image)
            assert compare_images(path / filename, gen / filename, 0.1) is None

    return _compare
