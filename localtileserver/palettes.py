from operator import attrgetter

import palettable


SIMPLE_PALETTES = {
    "red": ["#000", "#f00"],
    "r": ["#000", "#f00"],
    "green": ["#000", "#0f0"],
    "g": ["#000", "#0f0"],
    "blue": ["#000", "#00f"],
    "b": ["#000", "#00f"],
}


def is_palettable_palette(palette: str):
    try:
        attrgetter(palette)(palettable)
    except AttributeError:
        return False
    return True


def is_valid_palette(palette: str):
    return is_palettable_palette(palette) or palette in SIMPLE_PALETTES
