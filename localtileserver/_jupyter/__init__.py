"""
Jupyter Server extension that registers the localtileserver loopback proxy.

The proxy, URL autodetect, and auth handling all live in
:mod:`jupyter_loopback`. This module just wires them up for the
``localtileserver`` namespace so that ``<base_url>/localtileserver-proxy/<port>/...``
forwards to the in-kernel tile server.
"""

from jupyter_loopback import setup_proxy_handler

__all__ = ["_jupyter_server_extension_points", "_load_jupyter_server_extension"]


def _jupyter_server_extension_points() -> list[dict[str, str]]:
    """Declare this package as a Jupyter Server extension."""
    return [{"module": "localtileserver._jupyter"}]


def _load_jupyter_server_extension(server_app) -> None:
    """Register the loopback proxy for the ``localtileserver`` namespace."""
    setup_proxy_handler(server_app.web_app, namespace="localtileserver")
    server_app.log.info(
        "localtileserver: proxy registered at %slocaltileserver-proxy/<port>/...",
        server_app.web_app.settings.get("base_url", "/"),
    )
