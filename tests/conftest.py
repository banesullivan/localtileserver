import pytest

from tileserver.examples import get_bahamas, get_blue_marble, get_data_path


@pytest.fixture
def bahamas_file():
    return get_data_path("bahamas_rgb.tif")


@pytest.fixture
def bahamas(port="default", debug=True):
    # Using debug True since in a testing environment
    return get_bahamas(port=port, debug=debug)


@pytest.fixture
def blue_marble(port="default", debug=True):
    # Using debug True since in a testing environment
    return get_blue_marble(port=port, debug=debug)
