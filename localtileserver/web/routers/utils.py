"""
Shared utilities for FastAPI routers.
"""

from localtileserver.tiler.data import get_sf_bay_url
from localtileserver.tiler.utilities import get_clean_filename


def get_clean_filename_from_params(filename: str | None = None) -> str:
    """
    Clean and validate a filename from query parameters.

    Parameters
    ----------
    filename : str, optional
        Raw filename string from the request. If ``None`` or empty, the
        default sample dataset URL is used.

    Returns
    -------
    str
        Cleaned and validated filename or path.
    """
    if not filename:
        return get_clean_filename(get_sf_bay_url())
    return get_clean_filename(filename)


def parse_style_params(
    indexes: str | None = None,
    colormap: str | None = None,
    vmin: str | None = None,
    vmax: str | None = None,
    nodata: str | None = None,
) -> dict:
    """
    Parse style query parameters into a dict for handler functions.

    Handles the conversion from raw query strings (possibly with ``.0``, ``.1``
    suffixes for multi-value params) into the format expected by the tiler
    handler functions.

    Parameters
    ----------
    indexes : str, optional
        Comma-separated band indexes (e.g., ``"1"`` or ``"1,2,3"``).
    colormap : str, optional
        Name of the colormap to apply.
    vmin : str, optional
        Minimum value(s) for colormap stretching. May be comma-separated
        for multi-band.
    vmax : str, optional
        Maximum value(s) for colormap stretching. May be comma-separated
        for multi-band.
    nodata : str, optional
        Nodata value(s). May be comma-separated for multi-band.

    Returns
    -------
    dict
        Parsed style parameters ready for tiler handler functions.
    """
    out = {}
    if indexes is not None:
        # Could be "1" or "1,2,3" style
        try:
            parts = [s.strip() for s in indexes.split(",")]
            if len(parts) == 1:
                out["indexes"] = parts[0]
            else:
                out["indexes"] = parts
        except (ValueError, AttributeError):
            out["indexes"] = indexes
    if colormap is not None:
        out["colormap"] = colormap
    if vmin is not None:
        if "," in str(vmin):
            out["vmin"] = [s.strip() for s in vmin.split(",")]
        else:
            out["vmin"] = vmin
    if vmax is not None:
        if "," in str(vmax):
            out["vmax"] = [s.strip() for s in vmax.split(",")]
        else:
            out["vmax"] = vmax
    if nodata is not None:
        if "," in str(nodata):
            out["nodata"] = [s.strip() for s in nodata.split(",")]
        else:
            out["nodata"] = nodata
    return out
