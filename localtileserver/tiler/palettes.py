import logging
from operator import attrgetter
import re

import palettable

try:
    import cmocean  # noqa
except ImportError:
    pass
try:
    import colorcet  # noqa
except ImportError:
    pass

logger = logging.getLogger(__name__)

SIMPLE_PALETTES = {
    "red": ["#000", "#f00"],
    "r": ["#000", "#f00"],
    "green": ["#000", "#0f0"],
    "g": ["#000", "#0f0"],
    "blue": ["#000", "#00f"],
    "b": ["#000", "#00f"],
}


def is_hex_str(color: str):
    """Check if str is hex color."""
    if re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color):
        return True
    return False


def is_palettable_palette(name: str):
    try:
        attrgetter(name)(palettable)
    except AttributeError:
        return False
    return True


def is_mpl_cmap(name: str):
    """This will silently fail if matplotlib is not installed."""
    try:
        import matplotlib

        matplotlib.colormaps.get_cmap(name)
        return True
    except ImportError:  # pragma: no cover
        logger.error("Install matplotlib for additional colormap choices.")
    except ValueError:
        pass
    return False


def is_valid_palette_name(name: str):
    # return is_palettable_palette(name) or name in SIMPLE_PALETTES or is_mpl_cmap(name)
    return is_mpl_cmap(name)


def palette_valid_or_raise(name: str):
    status = False
    if isinstance(name, str):
        status = is_valid_palette_name(name)
    # elif isinstance(name, (list, tuple)):
    #     status = all([is_valid_palette_name(p) for p in name]) or all([is_hex_str(p) for p in name])
    if not status:
        raise ValueError(
            f"Please use a valid matplotlib colormap name or palettable palette name. Invalid: {name}"
        )


def get_palettes():
    """List of available palettes.

    This does not currently list the palettable palettes there isn't a clean
    way to list all of them.

    """
    cmaps = {}
    try:
        import matplotlib.pyplot

        cmaps["matplotlib"] = list(matplotlib.pyplot.colormaps())
    except ImportError:  # pragma: no cover
        logger.error("Install matplotlib for additional colormap choices.")
    cmaps["simple"] = [s for s in SIMPLE_PALETTES.keys() if len(s) > 1]
    return cmaps
