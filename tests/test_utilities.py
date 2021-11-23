from tileserver import Report
from tileserver.utilities import is_valid_palette


def test_is_valid_palette():
    assert is_valid_palette("matplotlib.Viridis_20")
    assert not is_valid_palette("foobar")


def test_report():
    assert Report()
