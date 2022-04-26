import logging

from osgeo_utils.samples.validate_cloud_optimized_geotiff import (
    ValidateCloudOptimizedGeoTIFFException,
    validate as gdal_validate,
)

from localtileserver.tileserver import get_clean_filename

logger = logging.getLogger(__name__)


def validate_cog(
    path, check_tiled: bool = True, full_check: bool = False, strict: bool = True, warn: bool = True
):
    path = get_clean_filename(path)
    warnings, errors, details = gdal_validate(path, check_tiled=check_tiled, full_check=full_check)
    if errors:
        raise ValidateCloudOptimizedGeoTIFFException(errors)
    if strict and warnings:
        raise ValidateCloudOptimizedGeoTIFFException(warnings)
    if warn:
        for warning in warnings:
            logger.warning(warning)
    return True
