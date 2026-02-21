"""Methods for working with images."""

import json
import pathlib

from matplotlib.colors import Colormap, LinearSegmentedColormap, ListedColormap
import numpy as np
import rasterio
from rasterio.enums import ColorInterp
from rio_tiler.colormap import cmap
from rio_tiler.io import Reader
from rio_tiler.models import ImageData

from .palettes import get_registered_colormap
from .utilities import ImageBytes, get_clean_filename, make_crs

# Some GDAL options to consider setting:
# - GDAL_ENABLE_WMS_CACHE="YES"
# - GDAL_DEFAULT_WMS_CACHE_PATH=str(get_cache_dir() / "gdalwmscache"))
# - GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"
# - GDAL_HTTP_UNSAFESSL="YES"


def get_reader(path: pathlib.Path | str) -> Reader:
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


def _handle_band_indexes(tile_source: Reader, indexes: list[int] | None = None):
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


def _handle_nodata(tile_source: Reader, nodata: int | float | None = None):
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
    indexes: list[int],
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
) -> tuple[dict[int, float], dict[int, float]]:
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
    return dict(zip(indexes, vmin, strict=True)), dict(zip(indexes, vmax, strict=True))


STRETCH_MODES = {"none", "minmax", "linear", "equalize", "sqrt", "log"}


def _apply_stretch(img: ImageData, stretch: str, tile_source: Reader, indexes: list[int]):
    """Apply a stretch mode to the image data in-place, returning adjusted vmin/vmax dicts."""
    if stretch == "none":
        return {i: 0 for i in indexes}, {i: 255 for i in indexes}
    stats = tile_source.statistics(indexes=indexes)
    if stretch == "minmax":
        vmin = {i: stats[f"b{i}"].min for i in indexes}
        vmax = {i: stats[f"b{i}"].max for i in indexes}
    elif stretch == "linear":
        # 2nd to 98th percentile stretch
        vmin = {i: stats[f"b{i}"].percentile_2 for i in indexes}
        vmax = {i: stats[f"b{i}"].percentile_98 for i in indexes}
    elif stretch == "equalize":
        # Histogram equalization via numpy
        for band_idx, band_num in enumerate(indexes):
            band_data = img.data[band_idx].astype(float)
            mask = img.mask[0] if img.mask.ndim == 3 else img.mask
            valid = band_data[mask > 0] if mask.any() else band_data.ravel()
            if valid.size > 0:
                sorted_vals = np.sort(valid)
                cdf = np.searchsorted(sorted_vals, band_data) / max(len(sorted_vals), 1)
                img.data[band_idx] = (cdf * 255).astype(img.data.dtype)
        return {i: 0 for i in indexes}, {i: 255 for i in indexes}
    elif stretch == "sqrt":
        vmin = {i: stats[f"b{i}"].min for i in indexes}
        vmax = {i: stats[f"b{i}"].max for i in indexes}
        for band_idx, band_num in enumerate(indexes):
            band_data = img.data[band_idx].astype(float)
            lo, hi = vmin[band_num], vmax[band_num]
            if hi > lo:
                normalized = np.clip((band_data - lo) / (hi - lo), 0, 1)
                img.data[band_idx] = (np.sqrt(normalized) * 255).astype(img.data.dtype)
        return {i: 0 for i in indexes}, {i: 255 for i in indexes}
    elif stretch == "log":
        vmin = {i: stats[f"b{i}"].min for i in indexes}
        vmax = {i: stats[f"b{i}"].max for i in indexes}
        for band_idx, band_num in enumerate(indexes):
            band_data = img.data[band_idx].astype(float)
            lo, hi = vmin[band_num], vmax[band_num]
            if hi > lo:
                normalized = np.clip((band_data - lo) / (hi - lo), 0, 1)
                img.data[band_idx] = (np.log1p(normalized * 254) / np.log(255) * 255).astype(
                    img.data.dtype
                )
        return {i: 0 for i in indexes}, {i: 255 for i in indexes}
    else:
        raise ValueError(f"Invalid stretch mode: {stretch!r}. Must be one of {STRETCH_MODES}.")
    return vmin, vmax


def _render_image(
    tile_source: Reader,
    img: ImageData,
    indexes: list[int],
    vmin: dict[int, float | None],
    vmax: dict[int, float | None],
    colormap: str | None = None,
    img_format: str = "PNG",
    stretch: str | None = None,
):
    # Resolve colormap to a dict for rio-tiler rendering
    registered = get_registered_colormap(colormap) if isinstance(colormap, str) else None
    if registered is not None:
        colormap = registered
    elif colormap in cmap.list():
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

    # Apply stretch mode if specified (overrides vmin/vmax)
    if stretch and stretch != "none":
        vmin, vmax = _apply_stretch(img, stretch, tile_source, indexes)

    if (
        not colormap
        and len(indexes) == 1
        and tile_source.dataset.colorinterp[indexes[0] - 1] == ColorInterp.palette
    ):
        # NOTE: vmin/vmax are not used for palette images
        colormap = tile_source.dataset.colormap(indexes[0])
    elif (
        img.data.dtype != np.dtype("uint8")
        or any(v is not None for v in vmin.values())
        or any(v is not None for v in vmax.values())
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
    indexes: list[int] | None = None,
    colormap: str | None = None,
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
    nodata: int | float | None = None,
    img_format: str = "PNG",
    expression: str | None = None,
    stretch: str | None = None,
):
    if expression:
        nodata = _handle_nodata(tile_source, nodata)
        img = tile_source.tile(x, y, z, expression=expression, nodata=nodata)
        expr_indexes = list(range(1, img.count + 1))
        vmin, vmax = _handle_vmin_vmax(expr_indexes, vmin, vmax)
        return _render_image(
            tile_source,
            img,
            indexes=expr_indexes,
            vmin=vmin,
            vmax=vmax,
            colormap=colormap,
            img_format=img_format,
            stretch=stretch,
        )
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
        stretch=stretch,
    )


def get_statistics(
    tile_source: Reader,
    indexes: list[int] | None = None,
    expression: str | None = None,
    **kwargs,
):
    """Get per-band statistics (min, max, mean, std, histogram).

    Returns a dict keyed by band name (e.g., 'b1', 'b2').
    """
    stats_kwargs = dict(kwargs)
    if expression:
        stats = tile_source.statistics(expression=expression, **stats_kwargs)
    else:
        if indexes is not None:
            if isinstance(indexes, (str, int)):
                indexes = [int(indexes)]
            else:
                indexes = [int(i) for i in indexes]
            stats_kwargs["indexes"] = indexes
        stats = tile_source.statistics(**stats_kwargs)
    result = {}
    for band_name, band_stats in stats.items():
        if hasattr(band_stats, "model_dump"):
            result[band_name] = band_stats.model_dump()
        else:
            result[band_name] = band_stats.dict()
    return result


def get_part(
    tile_source: Reader,
    bbox: tuple[float, float, float, float],
    indexes: list[int] | None = None,
    colormap: str | None = None,
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
    nodata: int | float | None = None,
    img_format: str = "PNG",
    max_size: int = 1024,
    dst_crs: str | None = None,
    bounds_crs: str | None = None,
    expression: str | None = None,
    stretch: str | None = None,
):
    """Extract a spatial subset (bounding box crop) from the raster.

    Parameters
    ----------
    bbox : tuple
        Bounding box as (left, bottom, right, top).
    dst_crs : str, optional
        Target CRS for the output image.
    bounds_crs : str, optional
        CRS of the bbox coordinates. Defaults to the dataset's native CRS.
    """
    nodata = _handle_nodata(tile_source, nodata)
    crs_obj = make_crs(dst_crs) if dst_crs else None
    bounds_crs_obj = make_crs(bounds_crs) if bounds_crs else tile_source.dataset.crs
    part_kwargs = {"max_size": max_size, "nodata": nodata, "bounds_crs": bounds_crs_obj}
    if crs_obj:
        part_kwargs["dst_crs"] = crs_obj
    if expression:
        img = tile_source.part(bbox, expression=expression, **part_kwargs)
        expr_indexes = list(range(1, img.count + 1))
        vmin_d, vmax_d = _handle_vmin_vmax(expr_indexes, vmin, vmax)
        return _render_image(
            tile_source, img, indexes=expr_indexes, vmin=vmin_d, vmax=vmax_d,
            colormap=colormap, img_format=img_format, stretch=stretch,
        )
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    vmin_d, vmax_d = _handle_vmin_vmax(indexes, vmin, vmax)
    img = tile_source.part(bbox, indexes=indexes, **part_kwargs)
    return _render_image(
        tile_source, img, indexes=indexes, vmin=vmin_d, vmax=vmax_d,
        colormap=colormap, img_format=img_format, stretch=stretch,
    )


def get_feature(
    tile_source: Reader,
    geojson: dict,
    indexes: list[int] | None = None,
    colormap: str | None = None,
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
    nodata: int | float | None = None,
    img_format: str = "PNG",
    max_size: int = 1024,
    dst_crs: str | None = None,
    expression: str | None = None,
    stretch: str | None = None,
):
    """Extract data masked to a GeoJSON feature.

    Parameters
    ----------
    geojson : dict
        A GeoJSON Feature or Geometry dict.
    """
    nodata = _handle_nodata(tile_source, nodata)
    crs_obj = make_crs(dst_crs) if dst_crs else None
    # Normalize to a Feature if given a bare geometry
    if "type" in geojson and geojson["type"] != "Feature":
        geojson = {"type": "Feature", "geometry": geojson, "properties": {}}
    feature_kwargs = {"shape": geojson}
    if crs_obj:
        feature_kwargs["dst_crs"] = crs_obj
    feature_kwargs["max_size"] = max_size
    if expression:
        img = tile_source.feature(expression=expression, nodata=nodata, **feature_kwargs)
        expr_indexes = list(range(1, img.count + 1))
        vmin_d, vmax_d = _handle_vmin_vmax(expr_indexes, vmin, vmax)
        return _render_image(
            tile_source, img, indexes=expr_indexes, vmin=vmin_d, vmax=vmax_d,
            colormap=colormap, img_format=img_format, stretch=stretch,
        )
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    vmin_d, vmax_d = _handle_vmin_vmax(indexes, vmin, vmax)
    img = tile_source.feature(indexes=indexes, nodata=nodata, **feature_kwargs)
    return _render_image(
        tile_source, img, indexes=indexes, vmin=vmin_d, vmax=vmax_d,
        colormap=colormap, img_format=img_format, stretch=stretch,
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
    colormap: str | None = None,
    vmin: float | list[float] | None = None,
    vmax: float | list[float] | None = None,
    nodata: int | float | None = None,
    img_format: str = "PNG",
    max_size: int = 512,
    crs: str | None = None,
    expression: str | None = None,
    stretch: str | None = None,
):
    if expression:
        nodata = _handle_nodata(tile_source, nodata)
        if crs is not None:
            dst_crs = make_crs(crs)
            src_bounds = tile_source.dataset.bounds
            src_crs = tile_source.dataset.crs
            if src_crs:
                dst_bounds = rasterio.warp.transform_bounds(src_crs, dst_crs, *src_bounds)
            else:
                dst_bounds = src_bounds
            img = tile_source.part(
                dst_bounds, dst_crs=dst_crs, max_size=max_size, expression=expression, nodata=nodata
            )
        else:
            img = tile_source.preview(max_size=max_size, expression=expression, nodata=nodata)
        expr_indexes = list(range(1, img.count + 1))
        vmin, vmax = _handle_vmin_vmax(expr_indexes, vmin, vmax)
        return _render_image(
            tile_source,
            img,
            indexes=expr_indexes,
            vmin=vmin,
            vmax=vmax,
            colormap=colormap,
            img_format=img_format,
            stretch=stretch,
        )
    if colormap is not None and indexes is None:
        indexes = [1]
    indexes = _handle_band_indexes(tile_source, indexes)
    nodata = _handle_nodata(tile_source, nodata)
    vmin, vmax = _handle_vmin_vmax(indexes, vmin, vmax)
    if crs is not None:
        dst_crs = make_crs(crs)
        src_bounds = tile_source.dataset.bounds
        src_crs = tile_source.dataset.crs
        if src_crs:
            dst_bounds = rasterio.warp.transform_bounds(src_crs, dst_crs, *src_bounds)
        else:
            dst_bounds = src_bounds
        img = tile_source.part(
            dst_bounds, dst_crs=dst_crs, max_size=max_size, indexes=indexes, nodata=nodata
        )
    else:
        img = tile_source.preview(max_size=max_size, indexes=indexes, nodata=nodata)
    return _render_image(
        tile_source,
        img,
        indexes=indexes,
        vmin=vmin,
        vmax=vmax,
        colormap=colormap,
        img_format=img_format,
        stretch=stretch,
    )
