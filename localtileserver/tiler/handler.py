"""Methods for working with images."""
import pathlib
from typing import List, Optional, Union

import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from rio_tiler.colormap import cmap
from rio_tiler.io import Reader
from rio_tiler.models import ImageData

from .utilities import ImageBytes, get_clean_filename, make_crs

# gdal.SetConfigOption("GDAL_ENABLE_WMS_CACHE", "YES")
# gdal.SetConfigOption("GDAL_DEFAULT_WMS_CACHE_PATH", str(get_cache_dir() / "gdalwmscache"))
# TODO: what's the other option for directories on S3?
# TODO: should I set these in a rasterio.Env?


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
            indexes = [int(i) for i in indexes]
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


def _render_image(
    tile_source: Reader,
    img: ImageData,
    indexes: Optional[List[int]] = None,
    colormap: Optional[str] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    img_format: str = "PNG",
):
    if isinstance(vmin, str):
        vmin = float(vmin)
    if isinstance(vmax, str):
        vmax = float(vmax)
    colormap = cmap.get(colormap) if colormap else None
    if (
        not colormap
        and len(indexes) == 1
        and tile_source.dataset.colorinterp[indexes[0] - 1] == ColorInterp.palette
    ):
        colormap = tile_source.dataset.colormap(indexes[0])
    elif img.data.dtype != np.dtype("uint8") or vmin is not None or vmax is not None:
        stats = tile_source.statistics()
        in_range = [
            (s.min if vmin is None else vmin, s.max if vmax is None else vmax)
            for s in stats.values()
        ]
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
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    nodata: Optional[Union[int, float]] = None,
    img_format: str = "PNG",
):
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    nodata = _handle_nodata(tile_source, nodata)
    img = tile_source.tile(x, y, z, indexes=indexes, nodata=nodata)
    return _render_image(
        tile_source,
        img,
        indexes=indexes,
        colormap=colormap,
        img_format=img_format,
        vmin=vmin,
        vmax=vmax,
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
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    nodata: Optional[Union[int, float]] = None,
    img_format: str = "PNG",
    max_size: int = 512,
):
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    nodata = _handle_nodata(tile_source, nodata)
    img = tile_source.preview(max_size=max_size, indexes=indexes, nodata=nodata)
    return _render_image(
        tile_source,
        img,
        indexes=indexes,
        colormap=colormap,
        img_format=img_format,
        vmin=vmin,
        vmax=vmax,
    )
