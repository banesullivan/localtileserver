"""Methods for working with images."""
from contextlib import contextmanager
import logging
import os
import pathlib
import tempfile
from typing import Union

import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from rio_tiler.colormap import cmap
from rio_tiler.io import Reader
from rio_tiler.models import ImageData

from .utilities import get_cache_dir, get_clean_filename, make_crs

logger = logging.getLogger(__name__)


# gdal.SetConfigOption("GDAL_ENABLE_WMS_CACHE", "YES")
# gdal.SetConfigOption("GDAL_DEFAULT_WMS_CACHE_PATH", str(get_cache_dir() / "gdalwmscache"))
# TODO: what's the other option for directories on S3?
# TODO: should I set these in a rasterio.Env?


def get_tile_source(path: Union[pathlib.Path, str]) -> Reader:
    return Reader(get_clean_filename(path))


@contextmanager
def yield_tile_source(path: Union[pathlib.Path, str]) -> Reader:
    with get_tile_source(path) as source:
        yield source


def get_meta_data(tile_source: Reader):
    metadata = tile_source.dataset.meta
    metadata.update(crs=metadata["crs"].to_wkt(), transform=list(metadata["transform"]))
    metadata["bounds"] = get_source_bounds(tile_source)
    return metadata


def _get_region(tile_source: Reader, region: dict, encoding: str):
    raise NotImplementedError
    result, mime_type = tile_source.getRegion(region=region, encoding=encoding)
    if encoding == "TILED":
        path = result
    else:
        # Write content to temporary file
        fd, path = tempfile.mkstemp(
            suffix=f".{encoding}", prefix="pixelRegion_", dir=str(get_cache_dir())
        )
        os.close(fd)
        path = pathlib.Path(path)
        with open(path, "wb") as f:
            f.write(result)
    return path, mime_type


def get_region_world(
    tile_source: Reader,
    left: float,
    right: float,
    bottom: float,
    top: float,
    units: str = "EPSG:4326",
    encoding: str = "TILED",
):
    region = dict(left=left, right=right, bottom=bottom, top=top, units=units)
    return _get_region(tile_source, region, encoding)


def get_source_bounds(tile_source: Reader, projection: str = "EPSG:4326", decimal_places: int = 6):
    src_crs = tile_source.dataset.crs
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
        "west": round(left, decimal_places),
        "south": round(bottom, decimal_places),
        "east": round(right, decimal_places),
        "north": round(top, decimal_places),
    }


def _handle_band_indexes(tile_source: Reader, indexes: list[int] | None = None):
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
    return indexes


def _handle_nodata(tile_source: Reader, nodata: int | float | None = None):
    floaty = False
    if any(dtype.startswith("float") for dtype in tile_source.dataset.dtypes):
        floaty = True
    if floaty and nodata is None and tile_source.dataset.nodata is not None:
        nodata = np.nan
    return nodata


def _render_image(
    tile_source: Reader,
    img: ImageData,
    indexes: list[int] = None,
    colormap: str | None = None,
    img_format: str = "PNG",
    vmin: float | None = None,
    vmax: float | None = None,
):
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
        print(in_range)
        img.rescale(
            in_range=in_range,
            out_range=[(0, 255)],
        )
    return img.render(img_format=img_format, colormap=colormap if colormap else None)


def get_tile(
    tile_source: Reader,
    z: int,
    x: int,
    y: int,
    indexes: list[int] | None = None,
    colormap: str | None = None,
    img_format: str = "PNG",
    nodata: int | float | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
):
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
    indexes: list[int] | None = None,
    max_size: int = 1024,
    colormap: str | None = None,
    img_format: str = "PNG",
    nodata: int | float | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
):
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
