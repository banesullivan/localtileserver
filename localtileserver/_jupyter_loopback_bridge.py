"""
Auto-wire jupyter-loopback's comm bridge so tile URLs reach the kernel
in webview-based Jupyter frontends.

``localtileserver`` bundles a jupyter-server extension that mounts the
HTTP proxy path defined by ``jupyter_loopback.setup_proxy_handler``. In
JupyterLab, JupyterHub, Binder, and Notebook 7 that's enough: the
notebook webview shares an origin with the jupyter-server, so the
browser can reach ``<base_url>/localtileserver-proxy/<port>/…``
directly. VS Code Jupyter (local or over Remote-SSH), Google Colab,
Shiny for Python, Solara, and marimo all render notebook outputs in a
sandboxed webview whose origin is **not** the jupyter-server. Those
root-relative URLs never reach the proxy, so the browser falls back to
``http://127.0.0.1:<port>/…`` and fails.

This module's :func:`enable_for_port` routes tile URLs through the
``jupyter_loopback`` comm bridge instead. The bridge opens a second
channel -- the kernel's own comm websocket -- and a small DOM shim
rewrites matching ``<img src>``, ``fetch``, and ``XMLHttpRequest`` calls
so they travel over that channel. Leaflet's ``createTile`` never
notices anything changed.

Calling this is idempotent and free where it's unneeded: in
jupyter-server environments the comm bridge simply sits idle because
the HTTP proxy already works. Users who want to opt out entirely can
set ``LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK=1`` in their environment.
"""

import logging
import os

import jupyter_loopback

logger = logging.getLogger(__name__)

# Ports already handed to :func:`jupyter_loopback.intercept_localhost`
# in this kernel. Deduplicating at this layer keeps tile-layer
# construction idempotent from the user's point of view -- repeated
# calls don't spam the cell output with redundant ``<script>`` tags.
_INTERCEPTED: set[int] = set()

# One-shot warning flags so users see a single actionable log line
# instead of either silence or a flood when their jupyter-loopback
# install is too old or missing its ``[comm]`` extra.
_warned_old_version = False
_warned_missing_extra = False


def _is_disabled() -> bool:
    """
    Return ``True`` if ``LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK`` opts out.
    """
    value = os.environ.get("LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK", "")
    return value.lower() not in ("", "0", "false", "no", "off")


def enable_for_port(port: int | None) -> None:
    """
    Install the jupyter-loopback interceptor for a single loopback port.

    Safe to call many times for the same port; only the first call
    actually emits the bridge widget and the interceptor ``<script>``.
    Silently no-ops when the user has set
    ``LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK`` or when ``port`` is
    ``None``.

    Parameters
    ----------
    port : int or None
        The loopback port of the tile server, typically
        :attr:`TileClient.server_port`.
    """
    global _warned_old_version, _warned_missing_extra

    if port is None or _is_disabled():
        return
    port_int = int(port)
    if port_int in _INTERCEPTED:
        return
    # ``intercept_localhost`` landed in jupyter-loopback 0.2 -- the bit
    # of the library that makes webview frontends actually work. If an
    # older install is present, log a single informative warning the
    # first time we notice so the user isn't left hunting silent
    # no-ops, then bail out.
    if not hasattr(jupyter_loopback, "intercept_localhost"):
        if not _warned_old_version:
            logger.warning(
                "localtileserver: jupyter-loopback %s lacks intercept_localhost; "
                "tile URLs won't be rerouted in VS Code / Colab / other webview "
                "frontends. Upgrade with `pip install -U jupyter-loopback[comm]`.",
                getattr(jupyter_loopback, "__version__", "unknown"),
            )
            _warned_old_version = True
        return
    try:
        if not jupyter_loopback.is_comm_bridge_enabled():
            jupyter_loopback.enable_comm_bridge()
        jupyter_loopback.intercept_localhost(port_int)
    except ImportError as exc:
        # Almost always means the ``[comm]`` extra (``anywidget``) is
        # missing. Surface it once, clearly, instead of letting the bridge
        # stay silently dormant in VS Code / Colab / other webview
        # frontends where the user expects tiles to work.
        if not _warned_missing_extra:
            logger.warning(
                "localtileserver: cannot enable jupyter-loopback comm bridge: %s. "
                "Install the comm extra so tiles work in VS Code / Colab / Shiny / "
                "Solara / marimo: `pip install jupyter-loopback[comm]`.",
                exc,
            )
            _warned_missing_extra = True
        return
    except Exception as exc:
        # Broad catch: ``enable_for_port`` is called from tile-layer
        # construction and must never break that flow. A surprising
        # bridge error (bad anywidget version, traitlets quirk, etc.)
        # degrades to "tiles still fail" rather than "import explodes".
        logger.debug("localtileserver: jupyter-loopback setup failed: %s", exc)
        return
    _INTERCEPTED.add(port_int)


def enable_jupyter_loopback(port: int | None = None) -> None:
    """
    Ensure the jupyter-loopback comm bridge is active for a tile server port.

    Most users will never need to call this directly:
    :func:`get_leaflet_tile_layer` and :func:`get_folium_tile_layer`
    do it automatically for the port of the client they wrap, and
    :meth:`TileClient.enable_jupyter_loopback` exposes it as a method
    on the client itself.

    Reach for this helper when you need the bridge active for a port
    that didn't flow through those code paths -- for instance, a
    :class:`TileServer` serving tiles consumed by a custom HTML output.
    Repeated calls with the same port are no-ops.

    Parameters
    ----------
    port : int or None, optional
        The loopback port to intercept. If omitted, this function is a
        no-op (pass an explicit ``None`` in programmatic code to make
        the intent clear).

    See Also
    --------
    jupyter_loopback.enable_comm_bridge : The underlying bridge installer.
    jupyter_loopback.intercept_localhost : The per-port URL rewriter.

    Notes
    -----
    Opt out of this behaviour globally by setting
    ``LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK=1`` in your environment
    before importing ``localtileserver``.
    """
    enable_for_port(port)
