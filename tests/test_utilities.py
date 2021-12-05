from localtileserver import Report
from localtileserver.palettes import is_valid_palette_name


def test_is_valid_palette_name():
    assert is_valid_palette_name("matplotlib.Viridis_20")
    assert not is_valid_palette_name("foobar")
    assert is_valid_palette_name("viridis")
    assert is_valid_palette_name("jet")


def test_report():
    assert Report()
