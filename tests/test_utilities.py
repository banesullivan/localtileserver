from osgeo_utils.samples.validate_cloud_optimized_geotiff import (
    ValidateCloudOptimizedGeoTIFFException,
)
import pytest

from localtileserver import Report, TileClient
from localtileserver.tileserver.palettes import (
    get_palette_by_name,
    get_palettes,
    is_valid_palette_name,
    mpl_to_palette,
)
from localtileserver.validate import validate_cog

has_mpl = False
try:
    import matplotlib  # noqa

    has_mpl = True
except ImportError:
    pass


def test_is_valid_palette_name():
    assert is_valid_palette_name("matplotlib.Viridis_20")
    assert not is_valid_palette_name("foobar")


@pytest.mark.skipif(not has_mpl, reason="matplotlib not installed.")
def test_mpl_colormaps():
    assert is_valid_palette_name("viridis")
    assert is_valid_palette_name("jet")
    assert len(mpl_to_palette("jet"))
    assert get_palette_by_name("jet")


def test_report():
    assert Report()


def test_get_palettes():
    assert isinstance(get_palettes(), dict)


def test_cog_validate(remote_file_url):
    assert validate_cog(remote_file_url)
    client = TileClient(remote_file_url)
    assert validate_cog(client)


def test_cog_validate_error(bahamas):
    with pytest.raises(ValidateCloudOptimizedGeoTIFFException):
        assert validate_cog(bahamas)
