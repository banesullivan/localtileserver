"""Mosaic support for localtileserver.

Provides virtual mosaics from multiple COG/raster files using
rio-tiler's ``mosaic_reader``.  No external ``cogeo-mosaic`` package
is required.
"""

from rio_tiler.io import Reader
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.mosaic.methods.defaults import FirstMethod

from .utilities import ImageBytes, get_clean_filename


def _tile_reader(asset: str, x: int, y: int, z: int, **kwargs):
    """Reader callable for mosaic_reader — reads a single tile."""
    with Reader(asset) as src:
        return src.tile(x, y, z, **kwargs)


def _preview_reader(asset: str, **kwargs):
    """Reader callable for mosaic_reader — reads a preview."""
    with Reader(asset) as src:
        return src.preview(**kwargs)


def get_mosaic_tile(
    assets: list[str],
    z: int,
    x: int,
    y: int,
    img_format: str = "PNG",
    indexes: list[int] | None = None,
    pixel_selection=None,
    **kwargs,
):
    """Get a mosaic tile from multiple raster assets.

    Parameters
    ----------
    assets : list[str]
        List of file paths or URLs.
    pixel_selection : MosaicMethodBase, optional
        Mosaic pixel selection method.  Defaults to ``FirstMethod``
        (first valid pixel wins).
    """
    clean_assets = [str(get_clean_filename(a)) for a in assets]
    tile_kwargs = dict(kwargs)
    if indexes:
        tile_kwargs["indexes"] = indexes
    if pixel_selection is None:
        pixel_selection = FirstMethod
    img, _ = mosaic_reader(
        clean_assets, _tile_reader, x, y, z,
        pixel_selection=pixel_selection, **tile_kwargs,
    )
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )


def get_mosaic_preview(
    assets: list[str],
    img_format: str = "PNG",
    max_size: int = 512,
    indexes: list[int] | None = None,
    pixel_selection=None,
    **kwargs,
):
    """Get a mosaic preview from multiple raster assets."""
    clean_assets = [str(get_clean_filename(a)) for a in assets]
    preview_kwargs = dict(kwargs)
    preview_kwargs["max_size"] = max_size
    if indexes:
        preview_kwargs["indexes"] = indexes
    if pixel_selection is None:
        pixel_selection = FirstMethod
    img, _ = mosaic_reader(
        clean_assets, _preview_reader,
        pixel_selection=pixel_selection, **preview_kwargs,
    )
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )
