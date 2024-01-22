import json
import uuid

import numpy as np
import rasterio

from localtileserver.tiler import get_cache_dir


def get_extensions_from_driver(driver: str):
    d = rasterio.drivers.raster_driver_extensions()
    if driver not in d.values():
        raise KeyError(f"Driver {driver} not found.")
    return [k for k, v in d.items() if v == driver]


def numpy_to_raster(ras_meta, data, out_path: str = None):
    """Save new raster from a numpy array using the metadata of another raster.

    Note
    ----
    Requires ``rasterio``

    Parameters
    ----------
    ras_meta : dict
        Raster metadata
    data : np.ndarray
        The bands of data to save to the new raster
    out_path : Optional[str]
        The path for which to write the new raster. If ``None``, this will
        use a temporary file

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


def save_new_raster(src, data, out_path: str = None):
    """Save new raster from a numpy array using the metadata of another raster.

    Note
    ----
    Requires ``rasterio``

    Parameters
    ----------
    src : str, DatasetReader, TilerInterface
        The source rasterio data whose spatial reference will be copied
    data : np.ndarray
        The bands of data to save to the new raster
    out_path : Optional[str]
        The path for which to write the new raster. If ``None``, this will
        use a temporary file

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
    """Dump shapely.Polygon to GeoJSON."""
    # Safely import shapely
    try:
        from shapely.geometry import mapping
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `shapely`: {e}")

    features = [{"type": "Feature", "properties": {}, "geometry": mapping(polygon)}]
    return json.dumps(features)


def parse_shapely(context):
    """Convert GeoJSON-like or WKT to shapely object.

    Parameters
    ----------
    context : str, dict
        a GeoJSON-like dict, which provides a "type" member describing the type
        of the geometry and "coordinates" member providing a list of coordinates,
        or an object which implements __geo_interface__.
        If a string, falls back to inferring as Well Known Text (WKT).
    """
    try:
        from shapely.geometry import shape
        import shapely.wkb
        import shapely.wkt
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"Please install `shapely`: {e}")
    if isinstance(context, str):
        # Infer as WKT
        return shapely.wkt.loads(context)
    elif isinstance(context, bytes):
        # Infer as WKB
        return shapely.wkb.loads(context)
    return shape(context)


def hillshade(arr, azimuth=30, altitude=30):
    """Create hillshade from a numpy array containing elevation data.

    Note
    ----
    Originally sourced from earthpy: https://github.com/earthlab/earthpy/blob/9ad455e85002a2b026c78685329f8c5b360fde5a/earthpy/spatial.py#L564

    Parameters
    ----------
    arr : numpy array of shape (rows, columns)
        Numpy array with elevation values to be used to created hillshade.
    azimuth : float (default=30)
        The desired azimuth for the hillshade.
    altitude : float (default=30)
        The desired sun angle altitude for the hillshade.
    Returns
    -------
    numpy array
        A numpy array containing hillshade values.

    License
    -------
    BSD 3-Clause License

    Copyright (c) 2018, Earth Lab
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

    * Neither the name of the copyright holder nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    """
    try:
        x, y = np.gradient(arr)
    except ValueError:
        raise ValueError("Input array should be two-dimensional")

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
