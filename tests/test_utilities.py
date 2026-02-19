import pytest

from localtileserver import Report, TileClient
from localtileserver.tiler.palettes import get_palettes, is_rio_cmap
from localtileserver.validate import validate_cog

has_mpl = False
try:
    import matplotlib  # noqa

    has_mpl = True
except ImportError:
    pass


def test_is_valid_palette_name():
    assert is_rio_cmap("viridis")
    assert not is_rio_cmap("foobar")


@pytest.mark.skipif(not has_mpl, reason="matplotlib not installed.")
def test_mpl_colormaps():
    assert is_rio_cmap("viridis")
    assert is_rio_cmap("jet")


def test_report():
    assert Report()


def test_get_palettes():
    assert isinstance(get_palettes(), dict)


def test_cog_validate(bahamas_file):
    assert validate_cog(str(bahamas_file))


def test_cog_validate_client(bahamas):
    assert validate_cog(bahamas)
