"""
Client connection configuration from environment variables and autodetection.
"""

import logging
import os

from jupyter_loopback import autodetect_prefix

logger = logging.getLogger(__name__)

# Namespace passed to :func:`jupyter_loopback.setup_proxy_handler` in
# :mod:`localtileserver._jupyter`. The autodetect template must match.
_LOOPBACK_NAMESPACE = "localtileserver"


def get_default_client_params(
    host: str | None = None,
    port: int | None = None,
    prefix: str | None = None,
) -> tuple[str | None, int | None, str | None]:
    """
    Get default client connection parameters from environment and Jupyter context.

    Resolution order for each parameter:

    1. Explicit argument passed to this function
    2. ``LOCALTILESERVER_CLIENT_{HOST,PORT,PREFIX}`` environment variable
    3. Autodetection of the bundled Jupyter Server extension (prefix only)

    Parameters
    ----------
    host : str or None, optional
        The client host. If ``None``, falls back to the
        ``LOCALTILESERVER_CLIENT_HOST`` environment variable.
    port : int or None, optional
        The client port. If ``None``, falls back to the
        ``LOCALTILESERVER_CLIENT_PORT`` environment variable.
    prefix : str or None, optional
        The client URL prefix. If ``None``, falls back to the
        ``LOCALTILESERVER_CLIENT_PREFIX`` environment variable, then to
        :func:`jupyter_loopback.autodetect_prefix`.

    Returns
    -------
    tuple of (str or None, int or None, str or None)
        The resolved ``(host, port, prefix)`` values.
    """
    if (
        host is None
        and "LOCALTILESERVER_CLIENT_HOST" in os.environ
        and os.environ["LOCALTILESERVER_CLIENT_HOST"]
    ):
        host = str(os.environ["LOCALTILESERVER_CLIENT_HOST"])
    if (
        port is None
        and "LOCALTILESERVER_CLIENT_PORT" in os.environ
        and os.environ["LOCALTILESERVER_CLIENT_PORT"]
    ):
        port = int(os.environ["LOCALTILESERVER_CLIENT_PORT"])
    if (
        prefix is None
        and "LOCALTILESERVER_CLIENT_PREFIX" in os.environ
        and os.environ["LOCALTILESERVER_CLIENT_PREFIX"]
    ):
        prefix = str(os.environ["LOCALTILESERVER_CLIENT_PREFIX"])

    # Only attempt autodetection when neither host nor prefix are set,
    # so user-supplied overrides take precedence.
    if prefix is None and host is None:
        auto = autodetect_prefix(_LOOPBACK_NAMESPACE)
        if auto is not None:
            prefix = auto
            logger.debug("localtileserver: autodetected Jupyter proxy prefix %r", prefix)
    return host, port, prefix
