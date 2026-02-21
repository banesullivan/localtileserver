"""
Client connection configuration from environment variables.
"""

import os


def get_default_client_params(
    host: str | None = None, port: int | None = None, prefix: str | None = None
):
    """
    Get default client connection parameters from environment variables.

    Each parameter is resolved from the corresponding environment variable
    (``LOCALTILESERVER_CLIENT_HOST``, ``LOCALTILESERVER_CLIENT_PORT``,
    ``LOCALTILESERVER_CLIENT_PREFIX``) when the caller does not provide an
    explicit value.

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
        ``LOCALTILESERVER_CLIENT_PREFIX`` environment variable.

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
    return host, port, prefix
