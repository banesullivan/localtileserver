"""STAC Reader support for localtileserver."""

from rio_tiler.io import STACReader

from .utilities import ImageBytes


def get_stac_reader(url: str, **kwargs) -> STACReader:
    """Create a STACReader for a STAC item URL."""
    return STACReader(url, **kwargs)


def get_stac_info(reader: STACReader, assets: list[str] | None = None):
    """Get STAC item info (available assets, metadata)."""
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
    """Get per-asset/band statistics."""
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
    """Get a tile from a STAC item."""
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
    """Get a thumbnail/preview from a STAC item."""
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
