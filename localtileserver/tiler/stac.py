"""
STAC Reader support for localtileserver.
"""

from rio_tiler.io import STACReader

from .utilities import ImageBytes


def get_stac_reader(url: str, **kwargs) -> STACReader:
    """
    Create a STACReader for a STAC item URL.

    Parameters
    ----------
    url : str
        URL to a STAC item JSON document.
    **kwargs : dict, optional
        Additional keyword arguments passed to
        ``rio_tiler.io.STACReader``.

    Returns
    -------
    STACReader
        An open STACReader instance for the given STAC item.
    """
    return STACReader(url, **kwargs)


def get_stac_info(reader: STACReader, assets: list[str] | None = None):
    """
    Get STAC item info (available assets, metadata).

    Parameters
    ----------
    reader : STACReader
        An open STACReader instance.
    assets : list of str or None, optional
        Asset names to query. If ``None``, info for all assets is
        returned.

    Returns
    -------
    dict
        Dictionary mapping asset names to their metadata dictionaries.
    """
    if assets:
        info = reader.info(assets=assets)
    else:
        info = reader.info()
    result = {}
    for asset_name, asset_info in info.items():
        if hasattr(asset_info, "model_dump"):
            result[asset_name] = asset_info.model_dump()
        else:
            result[asset_name] = asset_info.dict()
    return result


def get_stac_statistics(
    reader: STACReader,
    assets: list[str] | None = None,
    **kwargs,
):
    """
    Get per-asset/band statistics.

    Parameters
    ----------
    reader : STACReader
        An open STACReader instance.
    assets : list of str or None, optional
        Asset names to compute statistics for. If ``None``, statistics
        for all assets are returned.
    **kwargs : dict, optional
        Additional keyword arguments passed to
        ``STACReader.statistics``.

    Returns
    -------
    dict
        Dictionary mapping asset/band keys to their statistics
        dictionaries.
    """
    stats_kwargs = dict(kwargs)
    if assets:
        stats_kwargs["assets"] = assets
    stats = reader.statistics(**stats_kwargs)
    result = {}
    for key, val in stats.items():
        if hasattr(val, "model_dump"):
            result[key] = val.model_dump()
        else:
            result[key] = val.dict()
    return result


def get_stac_tile(
    reader: STACReader,
    z: int,
    x: int,
    y: int,
    assets: list[str] | None = None,
    expression: str | None = None,
    img_format: str = "PNG",
    **kwargs,
):
    """
    Get a tile from a STAC item.

    Parameters
    ----------
    reader : STACReader
        An open STACReader instance.
    z : int
        Tile zoom level.
    x : int
        Tile column index.
    y : int
        Tile row index.
    assets : list of str or None, optional
        Asset names to read. If ``None``, the reader default is used.
    expression : str or None, optional
        Band math expression (e.g., ``"B04/B03"``).
    img_format : str, optional
        Output image format. Default is ``"PNG"``.
    **kwargs : dict, optional
        Additional keyword arguments passed to ``STACReader.tile``.

    Returns
    -------
    ImageBytes
        Rendered tile image bytes with MIME type metadata.
    """
    tile_kwargs = dict(kwargs)
    if assets:
        tile_kwargs["assets"] = assets
    if expression:
        tile_kwargs["expression"] = expression
    img = reader.tile(x, y, z, **tile_kwargs)
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )


def get_stac_preview(
    reader: STACReader,
    assets: list[str] | None = None,
    expression: str | None = None,
    img_format: str = "PNG",
    max_size: int = 512,
    **kwargs,
):
    """
    Get a thumbnail/preview from a STAC item.

    Parameters
    ----------
    reader : STACReader
        An open STACReader instance.
    assets : list of str or None, optional
        Asset names to read. If ``None``, the reader default is used.
    expression : str or None, optional
        Band math expression (e.g., ``"B04/B03"``).
    img_format : str, optional
        Output image format. Default is ``"PNG"``.
    max_size : int, optional
        Maximum dimension (width or height) of the preview image in
        pixels. Default is ``512``.
    **kwargs : dict, optional
        Additional keyword arguments passed to
        ``STACReader.preview``.

    Returns
    -------
    ImageBytes
        Rendered preview image bytes with MIME type metadata.
    """
    preview_kwargs = dict(kwargs)
    preview_kwargs["max_size"] = max_size
    if assets:
        preview_kwargs["assets"] = assets
    if expression:
        preview_kwargs["expression"] = expression
    img = reader.preview(**preview_kwargs)
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )
