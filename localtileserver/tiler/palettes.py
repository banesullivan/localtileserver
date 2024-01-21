import logging

try:
    import cmocean  # noqa
except ImportError:
    pass
try:
    import colorcet  # noqa
except ImportError:
    pass

logger = logging.getLogger(__name__)


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


def palette_valid_or_raise(name: str):
    if not is_mpl_cmap(name):
        raise ValueError(f"Please use a valid matplotlib colormap name. Invalid: {name}")


def get_palettes():
    """List of available palettes."""
    cmaps = {}
    try:
        import matplotlib.pyplot

        cmaps["matplotlib"] = list(matplotlib.pyplot.colormaps())
    except ImportError:  # pragma: no cover
        logger.error("Install matplotlib for additional colormap choices.")
    return cmaps
