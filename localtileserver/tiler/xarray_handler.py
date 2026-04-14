"""
Xarray/DataArray tile serving support for localtileserver.

Requires the ``xarray`` optional dependency group.
"""

try:
    from rio_tiler.io.xarray import XarrayReader
    import xarray as xr
except ImportError:  # pragma: no cover
    xr = None
    XarrayReader = None

from .utilities import ImageBytes


def _check_xarray():
    if xr is None:
        raise ImportError(
            "xarray and rioxarray are required for xarray tile serving. "
            "Install with: pip install localtileserver[xarray]"
        )


def get_xarray_reader(data_array) -> "XarrayReader":
    """
    Create an XarrayReader from an xarray DataArray.

    Parameters
    ----------
    data_array : xarray.DataArray
        A DataArray with spatial dimensions and CRS metadata
        (typically set via rioxarray's ``.rio.write_crs()``).

    Returns
    -------
    XarrayReader
        An open XarrayReader instance backed by the given DataArray.
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
    """
    Get a tile from an XarrayReader.

    Parameters
    ----------
    reader : XarrayReader
        An open XarrayReader instance.
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
    **kwargs : dict, optional
        Additional keyword arguments passed to
        ``XarrayReader.tile``.

    Returns
    -------
    ImageBytes
        Rendered tile image bytes with MIME type metadata.
    """
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
    """
    Get a thumbnail/preview from an XarrayReader.

    Parameters
    ----------
    reader : XarrayReader
        An open XarrayReader instance.
    img_format : str, optional
        Output image format. Default is ``"PNG"``.
    max_size : int, optional
        Maximum dimension (width or height) of the preview image in
        pixels. Default is ``512``.
    indexes : list of int or None, optional
        Band indexes to read (1-based). If ``None``, all bands are
        included.
    **kwargs : dict, optional
        Additional keyword arguments passed to
        ``XarrayReader.preview``.

    Returns
    -------
    ImageBytes
        Rendered preview image bytes with MIME type metadata.
    """
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
    """
    Get metadata/info from an XarrayReader.

    Parameters
    ----------
    reader : XarrayReader
        An open XarrayReader instance.

    Returns
    -------
    dict
        Dictionary of dataset metadata (bounds, data types, band
        information, etc.).
    """
    info = reader.info()
    if hasattr(info, "model_dump"):
        return info.model_dump()
    return info.dict()


def get_xarray_statistics(reader: "XarrayReader", indexes: list[int] | None = None, **kwargs):
    """
    Get statistics from an XarrayReader.

    Parameters
    ----------
    reader : XarrayReader
        An open XarrayReader instance.
    indexes : list of int or None, optional
        Band indexes to compute statistics for (1-based). If ``None``,
        statistics for all bands are returned.
    **kwargs : dict, optional
        Additional keyword arguments passed to
        ``XarrayReader.statistics``.

    Returns
    -------
    dict
        Dictionary mapping band keys to their statistics dictionaries.
    """
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
