import logging
from typing import Union

import large_image
from large_image.tilesource import FileTileSource

from localtileserver.client import BaseTileClient
from localtileserver.tileserver import get_clean_filename

logger = logging.getLogger(__name__)


def validate_cog(
    path: Union[str, FileTileSource, BaseTileClient],
    strict: bool = True,
    warn: bool = True,
):
    if isinstance(path, FileTileSource):
        src = path
    elif isinstance(path, BaseTileClient):
        path = path.filename
        src = large_image.open(path)
    else:
        path = get_clean_filename(path)
        src = large_image.open(path)
    return src.validateCOG(strict=strict, warn=warn)
