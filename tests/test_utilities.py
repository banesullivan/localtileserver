import pytest

from localtileserver import Report
from localtileserver.tileserver.palettes import (
    get_palette_by_name,
    is_valid_palette_name,
    mpl_to_palette,
)

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
