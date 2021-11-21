import pytest

from tileserver.examples import get_data_path, get_bahamas


@pytest.fixture
def bahamas_file():
    return get_data_path("bahamas_rgb.tif")


@pytest.fixture
def bahamas_tile_server(port=0, debug=True):
    # Using debug True since in a testing environment
    return get_bahamas(port=port, debug=debug)
