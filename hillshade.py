import numpy as np

# https://github.com/earthlab/earthpy/blob/9ad455e85002a2b026c78685329f8c5b360fde5a/earthpy/spatial.py#L564
def hillshade(arr, azimuth=30, altitude=30):
    """Create hillshade from a numpy array containing elevation data.
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
    Example
    -------
    .. plot::
        >>> import matplotlib.pyplot as plt
        >>> import rasterio as rio
        >>> import earthpy.spatial as es
        >>> from earthpy.io import path_to_example
        >>> with rio.open(path_to_example('rmnp-dem.tif')) as src:
        ...     dem = src.read()
        >>> print(dem.shape)
        (1, 187, 152)
        >>> squeezed_dem = dem.squeeze() # remove first dimension
        >>> print(squeezed_dem.shape)
        (187, 152)
        >>> shade = es.hillshade(squeezed_dem)
        >>> plt.imshow(shade, cmap="Greys")
        <matplotlib.image.AxesImage object at 0x...>
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

    shaded = np.sin(altituderad) * np.sin(slope) + np.cos(altituderad) * np.cos(
        slope
    ) * np.cos((azimuthrad - np.pi / 2.0) - aspect)

    return 255 * (shaded + 1) / 2
