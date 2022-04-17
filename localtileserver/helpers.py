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
