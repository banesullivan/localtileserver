import logging

from flask import current_app, request

from localtileserver.tiler import get_clean_filename
from localtileserver.tiler.data import get_sf_bay_url

logger = logging.getLogger(__name__)


def get_clean_filename_from_request(param_name: str = "filename", strict: bool = False):
    try:
        # First look for filename in URL params
        f = request.args.get(param_name)
        if not f:
            raise KeyError
        filename = get_clean_filename(f)
    except KeyError:
        # Backup to app.config
        try:
            filename = get_clean_filename(current_app.config[param_name])
        except KeyError:
            message = "No filename set in app config or URL params. Using sample data."
            if strict:
                raise OSError(message)
            # Fallback to sample data
            logger.error(message)
            filename = get_clean_filename(get_sf_bay_url())
    return filename
