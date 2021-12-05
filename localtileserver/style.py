from collections.abc import Iterable
import json
import logging
from operator import attrgetter
from typing import Union

import palettable

logger = logging.getLogger(__name__)

SIMPLE_PALETTES = {
    "red": ["#000", "#f00"],
    "r": ["#000", "#f00"],
    "green": ["#000", "#0f0"],
    "g": ["#000", "#0f0"],
    "blue": ["#000", "#00f"],
    "b": ["#000", "#00f"],
}


def reformat_style_query_parameters(args: dict):
    out = {}
    for k, v in args.items():
        name = k.split(".")[0]
        if name in out:
            out[name].append(v)
        else:
            out.setdefault(name, [v])
    # If not multiple, remove list
    for k, v in out.items():
        if len(v) == 1:
            out[k] = v[0]
    return out


def is_palettable_palette(palette: str):
    try:
        attrgetter(palette)(palettable)
    except AttributeError:
        return False
    return True


def is_valid_palette(palette: str):
    return is_palettable_palette(palette) or palette in SIMPLE_PALETTES


def make_single_band_style(
    band: int,
    vmin: Union[int, float] = None,
    vmax: Union[int, float] = None,
    palette: str = None,
    nodata: Union[int, float] = None,
):
    style = None
    if isinstance(band, (int, str)):
        band = int(band)
        # Check for 0-index:
        if band == 0:
            raise ValueError("0 is an invalid band index. Bands start at 1.")
        style = {"band": band}
        if vmin is not None:
            style["min"] = vmin
        if vmax is not None:
            style["max"] = vmax
        if nodata:
            style["nodata"] = nodata

        if palette and is_palettable_palette(palette):
            style["palette"] = palette
        elif palette in SIMPLE_PALETTES:
            style["palette"] = SIMPLE_PALETTES[palette]
        else:
            logger.error(
                f"Palette choice of {palette} is invalid. Check available palettes in the `palettable` package. Ignoring palette choice."
            )

    return style


def safe_get(obj, index):
    if isinstance(obj, (list, tuple)):
        try:
            return obj[index]
        except (TypeError, IndexError):
            return None
    return obj


def make_style(band, vmin=None, vmax=None, palette=None, nodata=None):
    style = None
    # Handle when user sets min/max/etc. but forgot band. Default to 1
    if not band and any(v is not None for v in [vmin, vmax, palette, nodata]):
        band = 1
    elif band == 0:
        return

    if isinstance(band, int):
        # Handle viewing single band
        style = make_single_band_style(band, vmin, vmax, palette, nodata)
    elif isinstance(band, Iterable):
        # Handle viewing multiple bands together
        style = {"bands": []}
        if palette is None and len(band) == 3:
            # Handle setting RGB by default
            palette = ["r", "g", "b"]
        for i, b in enumerate(band):
            vmi = safe_get(vmin, i)
            vma = safe_get(vmax, i)
            p = safe_get(palette, i)
            nod = safe_get(nodata, i)
            style["bands"].append(
                make_single_band_style(band[i], vmin=vmi, vmax=vma, palette=p, nodata=nod),
            )
    # Return JSON encoded
    if style:
        return json.dumps(style)