from typing import Union

from rio_cogeo import cog_validate
from rio_tiler.io import Reader

from localtileserver.client import TilerInterface
from localtileserver.tiler import get_clean_filename


def validate_cog(
    path: Union[str, Reader, TilerInterface],
    strict: bool = True,
    quiet: bool = False,
) -> bool:
    if isinstance(path, Reader):
        path = path.dataset.name
    elif isinstance(path, TilerInterface):
        path = path.filename
    else:
        path = get_clean_filename(path)
    return cog_validate(path, strict=strict, quiet=quiet)[0]
