import logging
from typing import Union

from rio_cogeo import cog_validate
from rio_tiler.io import Reader

from localtileserver.client import BaseTileClientInterface
from localtileserver.tiler import get_clean_filename

logger = logging.getLogger(__name__)


def validate_cog(
    path: Union[str, Reader, BaseTileClientInterface],
    strict: bool = True,
    quiet: bool = False,
):
    if isinstance(path, Reader):
        path = path.dataset.name
    elif isinstance(path, BaseTileClientInterface):
        path = path.filename
    else:
        path = get_clean_filename(path)
    return cog_validate(path, strict=strict, quiet=quiet)
