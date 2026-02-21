"""
Helper functions for raster data and geometry.
"""

import json
import uuid

import numpy as np
import rasterio

from localtileserver.tiler import get_cache_dir


def get_extensions_from_driver(driver: str):
    """
    Get file extensions associated with a rasterio driver.

    Parameters
    ----------
    driver : str
        The name of the rasterio driver.

    Returns
    -------
    list of str
        A list of file extensions that correspond to the given driver.

    Raises
    ------
    KeyError
        If the driver is not found in the rasterio driver registry.
    """
    d = rasterio.drivers.raster_driver_extensions()
    if driver not in d.values():
        raise KeyError(f"Driver {driver} not found.")
    return [k for k, v in d.items() if v == driver]


def numpy_to_raster(ras_meta, data, out_path: str | None = None):
    """
    Save new raster from a numpy array using the metadata of another raster.

    Parameters
    ----------
    ras_meta : dict
        Raster metadata.
    data : numpy.ndarray
        The bands of data to save to the new raster.
    out_path : str or None, optional
        The path for which to write the new raster. If ``None``, this will
        use a temporary file.

    Returns
    -------
    str or pathlib.Path
        The path to the written raster file.
    """
    if data.ndim == 2:
        data = data[np.newaxis, ...]

    ras_meta = ras_meta.copy()
    ras_meta.update({"count": data.shape[0]})
    ras_meta.update({"dtype": str(data.dtype)})
    ras_meta.update({"height": data.shape[1]})
    ras_meta.update({"width": data.shape[2]})
    ras_meta.update({"compress": "lzw"})
    ras_meta.update({"driver": "GTiff"})

    if not out_path:
        ext = get_extensions_from_driver(ras_meta["driver"])[0]
        out_path = get_cache_dir() / f"{uuid.uuid4()}.{ext}"

    with rasterio.open(out_path, "w", **ras_meta) as dst:
        for i, band in enumerate(data):
            dst.write(band, i + 1)

    return out_path


def save_new_raster(src, data, out_path: str | None = None):
    """
    Save new raster from a numpy array using the metadata of another raster.

    Parameters
    ----------
    src : str or rasterio.io.DatasetReaderBase or TilerInterface
        The source rasterio data whose spatial reference will be copied.
    data : numpy.ndarray
        The bands of data to save to the new raster.
    out_path : str or None, optional
        The path for which to write the new raster. If ``None``, this will
        use a temporary file.

    Returns
    -------
    str or pathlib.Path
        The path to the written raster file.
    """
    from localtileserver.client import TilerInterface

    if data.ndim == 2:
        data = data.reshape((1, *data.shape))
    if data.ndim != 3:
        raise AssertionError("data must be ndim 3: (bands, height, width)")

    if isinstance(src, TilerInterface):
        src = src.dataset
    if isinstance(src, rasterio.io.DatasetReaderBase):
        ras_meta = src.meta.copy()
    else:
        with rasterio.open(src, "r") as src:
            # Get metadata / spatial reference
            ras_meta = src.meta

    return numpy_to_raster(ras_meta, data, out_path)


def polygon_to_geojson(polygon) -> str:
    """
    Dump a shapely Polygon to a GeoJSON string.

    Parameters
    ----------
    polygon : shapely.geometry.Polygon
        The shapely polygon to convert.

    Returns
    -------
    str
        A GeoJSON-formatted string containing the polygon as a Feature.
    """
    # Safely import shapely
    try:
        from shapely.geometry import mapping
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `shapely`: {e}") from e

    features = [{"type": "Feature", "properties": {}, "geometry": mapping(polygon)}]
    return json.dumps(features)


def parse_shapely(context):
    """
    Convert GeoJSON-like or WKT to shapely object.

    Parameters
    ----------
    context : str or bytes or dict
        A GeoJSON-like dict, which provides a "type" member describing the type
        of the geometry and "coordinates" member providing a list of coordinates,
        or an object which implements ``__geo_interface__``.
        If a string, falls back to inferring as Well Known Text (WKT).
        If bytes, falls back to inferring as Well Known Binary (WKB).

    Returns
    -------
    shapely.geometry.BaseGeometry
        The parsed shapely geometry object.
    """
    try:
        from shapely.geometry import shape
        import shapely.wkb
        import shapely.wkt
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `shapely`: {e}") from e
    if isinstance(context, str):
        # Infer as WKT
        return shapely.wkt.loads(context)
    elif isinstance(context, bytes):
        # Infer as WKB
        return shapely.wkb.loads(context)
    return shape(context)


def hillshade(arr, azimuth=30, altitude=30):
    """
    Create hillshade from a numpy array containing elevation data.

    Originally sourced from earthpy (BSD 3-Clause, Copyright (c) 2018 Earth Lab).

    Parameters
    ----------
    arr : numpy.ndarray
        Numpy array of shape ``(rows, columns)`` with elevation values to be
        used to create the hillshade.
    azimuth : float, optional
        The desired azimuth for the hillshade. Default is 30.
    altitude : float, optional
        The desired sun angle altitude for the hillshade. Default is 30.

    Returns
    -------
    numpy.ndarray
        A numpy array containing hillshade values.
    """
    try:
        x, y = np.gradient(arr)
    except ValueError as e:
        raise ValueError("Input array should be two-dimensional") from e

    if azimuth <= 360.0:
        azimuth = 360.0 - azimuth
        azimuthrad = azimuth * np.pi / 180.0
    else:
        raise ValueError("Azimuth value should be less than or equal to 360 degrees")

    if altitude <= 90.0:
        altituderad = altitude * np.pi / 180.0
    else:
        raise ValueError("Altitude value should be less than or equal to 90 degrees")

    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)

    shaded = np.sin(altituderad) * np.sin(slope) + np.cos(altituderad) * np.cos(slope) * np.cos(
        (azimuthrad - np.pi / 2.0) - aspect
    )

    return 255 * (shaded + 1) / 2
