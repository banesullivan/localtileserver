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
# Each entry is ``(port, path_prefix_or_None)`` so switching the
# prefix for a previously-registered port still propagates.
_INTERCEPTED: set[tuple[int, str | None]] = set()

# One-shot warning flags so users see a single actionable log line
# instead of either silence or a flood when the ``jupyter-loopback``
# install is broken.
_warned_missing_extra = False


def _is_disabled() -> bool:
    """
    Return ``True`` if ``LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK`` opts out.
    """
    value = os.environ.get("LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK", "")
    return value.lower() not in ("", "0", "false", "no", "off")


def enable_for_port(port: int | None, *, path_prefix: str | None = None) -> None:
    """
    Install the jupyter-loopback interceptor for a single loopback port.

    Safe to call many times for the same ``(port, path_prefix)`` pair;
    only the first call actually emits the bridge widget and the
    interceptor ``<script>``. Silently no-ops when the user has set
    ``LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK`` or when ``port`` is
    ``None``.

    Parameters
    ----------
    port : int or None
        The loopback port of the tile server, typically
        :attr:`TileClient.server_port`.
    path_prefix : str or None, keyword-only, optional
        Absolute URL path (with ``{port}`` already substituted) that
        also routes to this loopback port through
        :func:`jupyter_loopback.setup_proxy_handler`'s HTTP proxy. When
        supplied, jupyter-loopback probes the prefix once to decide
        whether to route through the HTTP proxy (when the extension is
        loaded on the single-user server) or through the comm bridge
        (when it isn't, as in JupyterHub deployments whose single-user
        env differs from the kernel env). Passing the prefix here is
        what makes tile layers work end-to-end in those Hub setups.
    """
    global _warned_missing_extra

    if port is None or _is_disabled():
        return
    port_int = int(port)
    prefix_clean = (path_prefix or "").rstrip("/") or None
    key = (port_int, prefix_clean)
    if key in _INTERCEPTED:
        return
    try:
        if not jupyter_loopback.is_comm_bridge_enabled():
            jupyter_loopback.enable_comm_bridge()
        jupyter_loopback.intercept_localhost(port_int, path_prefix=prefix_clean)
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
    _INTERCEPTED.add(key)


def enable_jupyter_loopback(
    port: int | None = None,
    *,
    path_prefix: str | None = None,
) -> None:
    """
    Ensure the jupyter-loopback comm bridge is active for a tile server port.

    Most users will never need to call this directly:
    :func:`get_leaflet_tile_layer` and :func:`get_folium_tile_layer`
    do it automatically for the port (and autodetected proxy prefix)
    of the client they wrap, and
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
    path_prefix : str or None, keyword-only, optional
        The absolute URL path prefix that routes to this port via the
        HTTP proxy. Supply this on JupyterHub so the comm bridge can
        take over when the single-user server lacks the localtileserver
        extension.

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
    enable_for_port(port, path_prefix=path_prefix)
