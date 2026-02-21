"""Xarray/DataArray tile serving support for localtileserver.

Requires the ``xarray`` optional dependency group.
"""

try:
    import xarray as xr
    from rio_tiler.io.xarray import XarrayReader
except ImportError:  # pragma: no cover
    xr = None
    XarrayReader = None

from .utilities import ImageBytes


def _check_xarray():
    if xr is None:
        raise ImportError(
            "xarray and rioxarray are required for XarrayTileClient. "
            "Install with: pip install localtileserver[xarray]"
        )


def get_xarray_reader(data_array) -> "XarrayReader":
    """Create an XarrayReader from an xarray DataArray.

    Parameters
    ----------
    data_array : xarray.DataArray
        A DataArray with spatial dimensions and CRS metadata
        (typically set via rioxarray's ``.rio.write_crs()``).
    """
    _check_xarray()
    return XarrayReader(data_array)


def get_xarray_tile(
    reader: "XarrayReader",
    z: int,
    x: int,
    y: int,
    img_format: str = "PNG",
    indexes: list[int] | None = None,
    **kwargs,
):
    """Get a tile from an XarrayReader."""
    tile_kwargs = dict(kwargs)
    if indexes:
        tile_kwargs["indexes"] = indexes
    img = reader.tile(x, y, z, **tile_kwargs)
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )


def get_xarray_preview(
    reader: "XarrayReader",
    img_format: str = "PNG",
    max_size: int = 512,
    indexes: list[int] | None = None,
    **kwargs,
):
    """Get a thumbnail/preview from an XarrayReader."""
    preview_kwargs = dict(kwargs)
    preview_kwargs["max_size"] = max_size
    if indexes:
        preview_kwargs["indexes"] = indexes
    img = reader.preview(**preview_kwargs)
    return ImageBytes(
        img.render(img_format=img_format),
        mimetype=f"image/{img_format.lower()}",
    )


def get_xarray_info(reader: "XarrayReader"):
    """Get metadata/info from an XarrayReader."""
    info = reader.info()
    if hasattr(info, "model_dump"):
        return info.model_dump()
    return info.dict()


def get_xarray_statistics(reader: "XarrayReader", indexes: list[int] | None = None, **kwargs):
    """Get statistics from an XarrayReader."""
    stats_kwargs = dict(kwargs)
    if indexes:
        stats_kwargs["indexes"] = indexes
    stats = reader.statistics(**stats_kwargs)
    result = {}
    for key, val in stats.items():
        if hasattr(val, "model_dump"):
            result[key] = val.model_dump()
        else:
            result[key] = val.dict()
    return result
