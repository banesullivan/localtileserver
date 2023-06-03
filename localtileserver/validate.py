import logging
from typing import Union

import large_image
from large_image_source_rasterio import RasterioFileTileSource

from localtileserver.client import BaseTileClientInterface
from localtileserver.tiler import get_clean_filename

logger = logging.getLogger(__name__)


def validate_cog(
    path: Union[str, RasterioFileTileSource, BaseTileClientInterface],
    strict: bool = True,
    warn: bool = True,
):
    if isinstance(path, RasterioFileTileSource):
        src = path
    elif isinstance(path, BaseTileClientInterface):
        path = path.filename
        src = large_image.open(path)
    else:
        path = get_clean_filename(path)
        src = large_image.open(path)
    return src.validateCOG(strict=strict, warn=warn)
