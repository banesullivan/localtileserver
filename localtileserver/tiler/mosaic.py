"""
Mosaic support for localtileserver.

Provides virtual mosaics from multiple COG/raster files using
rio-tiler's ``mosaic_reader``.  No external ``cogeo-mosaic`` package
is required.
"""

from rio_tiler.io import Reader
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.mosaic.methods.defaults import FirstMethod

from .utilities import ImageBytes, get_clean_filename


def _tile_reader(asset: str, x: int, y: int, z: int, **kwargs):
    """
    Reader callable for mosaic_reader -- reads a single tile.
    """
    with Reader(asset) as src:
        return src.tile(x, y, z, **kwargs)


def _preview_reader(asset: str, **kwargs):
    """
    Reader callable for mosaic_reader -- reads a preview.
    """
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
    """
    Get a mosaic tile from multiple raster assets.

    Parameters
    ----------
    assets : list of str
        List of file paths or URLs to raster datasets.
    z : int
        Tile zoom level.
    x : int
        Tile column index.
    y : int
        Tile row index.
    img_format : str, optional
        Output image format. Default is ``"PNG"``.
    indexes : list of int or None, optional
        Band indexes to read (1-based). If ``None``, all bands are
        included.
    pixel_selection : MosaicMethodBase or None, optional
        Mosaic pixel selection method. Defaults to ``FirstMethod``
        (first valid pixel wins).
    **kwargs : dict, optional
        Additional keyword arguments passed to the underlying tile
        reader.

    Returns
    -------
    ImageBytes
        Rendered mosaic tile image bytes with MIME type metadata.
    """
    clean_assets = [str(get_clean_filename(a)) for a in assets]
    tile_kwargs = dict(kwargs)
    if indexes:
        tile_kwargs["indexes"] = indexes
    if pixel_selection is None:
        pixel_selection = FirstMethod
    img, _ = mosaic_reader(
        clean_assets,
        _tile_reader,
        x,
        y,
        z,
        pixel_selection=pixel_selection,
        **tile_kwargs,
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
    """
    Get a mosaic preview from multiple raster assets.

    Parameters
    ----------
    assets : list of str
        List of file paths or URLs to raster datasets.
    img_format : str, optional
        Output image format. Default is ``"PNG"``.
    max_size : int, optional
        Maximum dimension (width or height) of the preview image in
        pixels. Default is ``512``.
    indexes : list of int or None, optional
        Band indexes to read (1-based). If ``None``, all bands are
        included.
    pixel_selection : MosaicMethodBase or None, optional
        Mosaic pixel selection method. Defaults to ``FirstMethod``
        (first valid pixel wins).
    **kwargs : dict, optional
        Additional keyword arguments passed to the underlying preview
        reader.

    Returns
    -------
    ImageBytes
        Rendered mosaic preview image bytes with MIME type metadata.
    """
    clean_assets = [str(get_clean_filename(a)) for a in assets]
    preview_kwargs = dict(kwargs)
    preview_kwargs["max_size"] = max_size
    if indexes:
        preview_kwargs["indexes"] = indexes
    if pixel_selection is None:
        pixel_selection = FirstMethod
    img, _ = mosaic_reader(
        clean_assets,
        _preview_reader,
        pixel_selection=pixel_selection,
        **preview_kwargs,
    )
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )
