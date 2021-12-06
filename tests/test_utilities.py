import pytest

from localtileserver import Report
from localtileserver.palettes import is_valid_palette_name

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
def test_is_valid_mpl_name():
    assert is_valid_palette_name("viridis")
    assert is_valid_palette_name("jet")


def test_report():
    assert Report()
