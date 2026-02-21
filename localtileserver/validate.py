"""
Cloud Optimized GeoTIFF (COG) validation utilities.
"""

from rio_cogeo import cog_validate
from rio_tiler.io import Reader

from localtileserver.client import TilerInterface
from localtileserver.tiler import get_clean_filename


def validate_cog(
    path: str | Reader | TilerInterface,
    strict: bool = True,
    quiet: bool = False,
) -> bool:
    """
    Validate whether a raster file is a valid Cloud Optimized GeoTIFF (COG).

    Parameters
    ----------
    path : str or Reader or TilerInterface
        The path to the raster file, or an open ``rio_tiler.io.Reader`` or
        ``TilerInterface`` instance.
    strict : bool, optional
        Whether to use strict validation rules. Default is ``True``.
    quiet : bool, optional
        Whether to suppress validation output. Default is ``False``.

    Returns
    -------
    bool
        ``True`` if the file is a valid COG, ``False`` otherwise.
    """
    if isinstance(path, Reader):
        path = path.dataset.name
    elif isinstance(path, TilerInterface):
        path = path.filename
    else:
        path = get_clean_filename(path)
    return cog_validate(path, strict=strict, quiet=quiet)[0]
