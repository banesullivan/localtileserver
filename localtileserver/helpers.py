import json


def save_new_raster(src_path, out_path, data):
    """Save new raster from a numpy array using the metadata of another raster.

    Requires ``rasterio``

    Parameters
    ----------
    src_path : str
        The source data whose spatial reference will be copied
    out_path : str
        The path for which to write the new raster
    data : np.ndarray
        The bands of data to save to the new raster

    """
    import rasterio as rio

    if data.ndim == 2:
        data = data.reshape((1, *data.shape))
    if data.ndim != 3:
        raise AssertionError("data must be ndim 3: (bands, height, width)")

    with rio.open(src_path, "r") as src:
        # Get a copy of metadata / spatial reference
        ras_meta = src.meta.copy()

    ras_meta.update({"count": data.shape[0]})
    ras_meta.update({"dtype": str(data.dtype)})
    ras_meta.update({"height": data.shape[1]})
    ras_meta.update({"width": data.shape[2]})

    with rio.open(out_path, "w", **ras_meta) as dst:
        for i, band in enumerate(data):
            dst.write(band, i + 1)

    return out_path


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
