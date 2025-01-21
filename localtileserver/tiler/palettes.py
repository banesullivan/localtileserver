import logging

from rio_tiler.colormap import cmap as RIO_CMAPS

logger = logging.getLogger(__name__)


def is_rio_cmap(name: str):
    """Check whether cmap is supported by rio-tiler."""
    return name in RIO_CMAPS.data.keys()


def palette_valid_or_raise(name: str):
    if not is_rio_cmap(name):
        raise ValueError(f"Please use a valid rio-tiler registered colormap name. Invalid: {name}")


def get_palettes():
    """List of available palettes."""
    return {"matplotlib": list(RIO_CMAPS.data.keys())}
