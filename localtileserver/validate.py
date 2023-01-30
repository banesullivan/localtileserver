import logging
from typing import Union

from large_image.tilesource import FileTileSource

from localtileserver.client import BaseTileClient
from localtileserver.tileserver import get_clean_filename

logger = logging.getLogger(__name__)


def validate_cog(
    path: Union[str, FileTileSource, BaseTileClient],
    check_tiled: bool = True,
    full_check: bool = False,
    strict: bool = True,
    warn: bool = True,
):
    from osgeo_utils.samples.validate_cloud_optimized_geotiff import (
        ValidateCloudOptimizedGeoTIFFException,
        validate as gdal_validate,
    )

    if isinstance(path, FileTileSource):
        path = path._getLargeImagePath()
    elif isinstance(path, BaseTileClient):
        path = path.filename
    else:
        path = get_clean_filename(path)
    warnings, errors, details = gdal_validate(
        str(path), check_tiled=check_tiled, full_check=full_check
    )
    if errors:
        raise ValidateCloudOptimizedGeoTIFFException(errors)
    if strict and warnings:
        raise ValidateCloudOptimizedGeoTIFFException(warnings)
    if warn:
        for warning in warnings:
            logger.warning(warning)
    return True
