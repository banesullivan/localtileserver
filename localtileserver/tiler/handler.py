"""Methods for working with images."""
import json
import pathlib
from typing import Dict, List, Optional, Tuple, Union

from matplotlib.colors import Colormap, LinearSegmentedColormap, ListedColormap
import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from rio_tiler.colormap import cmap
from rio_tiler.io import Reader
from rio_tiler.models import ImageData

from .utilities import ImageBytes, get_clean_filename, make_crs

# Some GDAL options to consider setting:
# - GDAL_ENABLE_WMS_CACHE="YES"
# - GDAL_DEFAULT_WMS_CACHE_PATH=str(get_cache_dir() / "gdalwmscache"))
# - GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"
# - GDAL_HTTP_UNSAFESSL="YES"


def get_reader(path: Union[pathlib.Path, str]) -> Reader:
    return Reader(get_clean_filename(path))


def get_meta_data(tile_source: Reader):
    info = tile_source.info()
    if hasattr(info, "model_dump"):
        info = info.model_dump()
    else:
        info = info.dict()
    metadata = {
        **info,
        **tile_source.dataset.meta,
    }
    crs = metadata["crs"].to_wkt() if hasattr(metadata["crs"], "to_wkt") else None
    metadata.update(crs=crs, transform=list(metadata["transform"]))
    if crs:
        metadata["bounds"] = get_source_bounds(tile_source)
    return metadata


def get_source_bounds(tile_source: Reader, projection: str = "EPSG:4326", decimal_places: int = 6):
    src_crs = tile_source.dataset.crs
    if not src_crs:
        return {
            "left": -180.0,
            "bottom": -90.0,
            "right": 180.0,
            "top": 90.0,
        }
    dst_crs = make_crs(projection)
    left, bottom, right, top = rasterio.warp.transform_bounds(
        src_crs, dst_crs, *tile_source.dataset.bounds
    )
    return {
        "left": round(left, decimal_places),
        "bottom": round(bottom, decimal_places),
        "right": round(right, decimal_places),
        "top": round(top, decimal_places),
        # west, south, east, north
        # "west": round(left, decimal_places),
        # "south": round(bottom, decimal_places),
        # "east": round(right, decimal_places),
        # "north": round(top, decimal_places),
    }


def _handle_band_indexes(tile_source: Reader, indexes: Optional[List[int]] = None):
    band_names = [desc[0] for desc in tile_source.info().band_descriptions]

    def _index_lookup(index_or_name: str):
        try:
            return int(index_or_name)
        except ValueError:
            pass
        try:
            return band_names.index(index_or_name) + 1
        except ValueError:
            pass
        raise ValueError(f"Could not find band {index_or_name}")

    if not indexes:
        RGB_INTERPRETATIONS = [ColorInterp.red, ColorInterp.green, ColorInterp.blue]
        RGB_DESCRIPTORS = ["red", "green", "blue"]
        if set(RGB_INTERPRETATIONS).issubset(set(tile_source.dataset.colorinterp)):
            indexes = [tile_source.dataset.colorinterp.index(i) + 1 for i in RGB_INTERPRETATIONS]
        elif set(RGB_DESCRIPTORS).issubset(set(tile_source.dataset.descriptions)):
            indexes = [tile_source.dataset.descriptions.index(i) + 1 for i in RGB_DESCRIPTORS]
        elif len(tile_source.dataset.indexes) >= 3:
            indexes = [1, 2, 3]
        elif len(tile_source.dataset.indexes) < 3:
            indexes = [1]
        else:
            raise ValueError("Could not determine band indexes")
    else:
        if isinstance(indexes, str):
            indexes = int(indexes)
        if isinstance(indexes, int):
            indexes = [indexes]
        if isinstance(indexes, list):
            indexes = [_index_lookup(ind) for ind in indexes]
    return indexes


def _handle_nodata(tile_source: Reader, nodata: Optional[Union[int, float]] = None):
    floaty = False
    if any(dtype.startswith("float") for dtype in tile_source.dataset.dtypes):
        floaty = True
    if floaty and nodata is None and tile_source.dataset.nodata is not None:
        nodata = np.nan
    elif nodata is not None:
        if isinstance(nodata, str):
            nodata = float(nodata)
    return nodata


def _handle_vmin_vmax(
    indexes: List[int],
    vmin: Optional[Union[float, List[float]]] = None,
    vmax: Optional[Union[float, List[float]]] = None,
) -> Tuple[Dict[int, float], Dict[int, float]]:
    # TODO: move these string checks to the rest api
    if isinstance(vmin, (str, int)):
        vmin = float(vmin)
    if isinstance(vmax, (str, int)):
        vmax = float(vmax)
    if isinstance(vmin, list):
        vmin = [float(v) for v in vmin]
    if isinstance(vmax, list):
        vmax = [float(v) for v in vmax]
    if isinstance(vmin, float) or vmin is None:
        vmin = [vmin] * len(indexes)
    if isinstance(vmax, float) or vmax is None:
        vmax = [vmax] * len(indexes)
    # vmin/vmax must be list of values at this point
    if len(vmin) != len(indexes):
        raise ValueError("vmin must be same length as indexes")
    if len(vmax) != len(indexes):
        raise ValueError("vmax must be same length as indexes")
    # Now map to the band indexes
    return dict(zip(indexes, vmin)), dict(zip(indexes, vmax))


def _render_image(
    tile_source: Reader,
    img: ImageData,
    indexes: List[int],
    vmin: Dict[int, Optional[float]],
    vmax: Dict[int, Optional[float]],
    colormap: Optional[str] = None,
    img_format: str = "PNG",
):
    if colormap in cmap.list():
        colormap = cmap.get(colormap)
    elif isinstance(colormap, ListedColormap):
        c = LinearSegmentedColormap.from_list("", colormap.colors, N=256)
        colormap = {k: tuple(v) for k, v in enumerate(c(range(256), 1, 1))}
    elif isinstance(colormap, Colormap):
        colormap = {k: tuple(v) for k, v in enumerate(colormap(range(256), 1, 1))}
    elif colormap:
        c = json.loads(colormap)
        if isinstance(c, list):
            c = LinearSegmentedColormap.from_list("", c, N=256)
            colormap = {k: tuple(v) for k, v in enumerate(c(range(256), 1, 1))}
        else:
            colormap = {}
            for key, value in c.items():
                colormap[int(key)] = tuple(value)

    if (
        not colormap
        and len(indexes) == 1
        and tile_source.dataset.colorinterp[indexes[0] - 1] == ColorInterp.palette
    ):
        # NOTE: vmin/vmax are not used for palette images
        colormap = tile_source.dataset.colormap(indexes[0])
    # TODO: change these to any checks for none in vmin/vmax
    elif (
        img.data.dtype != np.dtype("uint8")
        or any(v is not None for v in vmin)
        or any(v is not None for v in vmax)
    ):
        stats = tile_source.statistics(indexes=indexes)
        in_range = []
        for i in indexes:
            in_range.append(
                (
                    stats[f"b{i}"].min if vmin[i] is None else vmin[i],
                    stats[f"b{i}"].max if vmax[i] is None else vmax[i],
                )
            )
        img.rescale(
            in_range=in_range,
            out_range=[(0, 255)],
        )
    return ImageBytes(
        img.render(img_format=img_format, colormap=colormap if colormap else None),
        mimetype=f"image/{img_format.lower()}",
    )


def get_tile(
    tile_source: Reader,
    z: int,
    x: int,
    y: int,
    indexes: Optional[List[int]] = None,
    colormap: Optional[str] = None,
    vmin: Optional[Union[float, List[float]]] = None,
    vmax: Optional[Union[float, List[float]]] = None,
    nodata: Optional[Union[int, float]] = None,
    img_format: str = "PNG",
):
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    nodata = _handle_nodata(tile_source, nodata)
    vmin, vmax = _handle_vmin_vmax(indexes, vmin, vmax)
    img = tile_source.tile(x, y, z, indexes=indexes, nodata=nodata)
    return _render_image(
        tile_source,
        img,
        indexes=indexes,
        vmin=vmin,
        vmax=vmax,
        colormap=colormap,
        img_format=img_format,
    )


def get_point(
    tile_source: Reader,
    lon: float,
    lat: float,
    **kwargs,
):
    return tile_source.point(lon, lat, **kwargs)


def get_preview(
    tile_source: Reader,
    indexes: Optional[List[int]] = None,
    colormap: Optional[str] = None,
    vmin: Optional[Union[float, List[float]]] = None,
    vmax: Optional[Union[float, List[float]]] = None,
    nodata: Optional[Union[int, float]] = None,
    img_format: str = "PNG",
    max_size: int = 512,
):
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    nodata = _handle_nodata(tile_source, nodata)
    vmin, vmax = _handle_vmin_vmax(indexes, vmin, vmax)
    img = tile_source.preview(max_size=max_size, indexes=indexes, nodata=nodata)
    return _render_image(
        tile_source,
        img,
        indexes=indexes,
        vmin=vmin,
        vmax=vmax,
        colormap=colormap,
        img_format=img_format,
    )
