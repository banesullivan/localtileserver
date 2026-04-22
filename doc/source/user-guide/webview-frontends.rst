.. _webview-frontends:

🪟 VS Code, Colab, and other webview notebooks
==============================================

``localtileserver`` works out of the box in JupyterLab, Notebook 7,
JupyterHub, and Binder because those frontends let the notebook browser
reach the jupyter-server origin directly. Root-relative tile URLs like
``/localtileserver-proxy/<port>/…`` resolve against the jupyter-server,
which routes them to the in-kernel tile server.

A handful of popular frontends do **not** share that origin with the
jupyter-server: VS Code Jupyter (including Remote-SSH), Google Colab,
Shiny for Python, Solara, and marimo all render notebook outputs in a
sandboxed webview. Root-relative URLs resolve to the webview's own
origin, so the proxy is invisible and the browser falls back to
``http://127.0.0.1:<port>/…`` -- which doesn't reach the kernel either.

How ``localtileserver`` fixes this
----------------------------------

``localtileserver`` integrates with
`jupyter-loopback <https://github.com/banesullivan/jupyter-loopback>`_
to open a second path: the notebook's own kernel comm channel. A small
DOM shim rewrites matching ``<img src>``, ``fetch``, and
``XMLHttpRequest`` calls so they travel over that comm channel instead
of the network. Leaflet's ``createTile`` doesn't know anything changed.

This is included in the core install -- ``pip install localtileserver``
pulls in ``jupyter-loopback[comm]`` automatically, so the typical
workflow requires nothing beyond what you're already doing:

.. code-block:: python

   from localtileserver import get_leaflet_tile_layer, TileClient

   client = TileClient('path/to/geo.tif')
   t = get_leaflet_tile_layer(client)

:func:`get_leaflet_tile_layer` and :func:`get_folium_tile_layer` both
automatically enable the comm bridge and register the client's port for
URL interception. No notebook changes required.

Using a ``TileClient`` without a widget helper
----------------------------------------------

If you're embedding raw tile URLs into custom HTML outputs (or using
anything other than the bundled ``get_*_tile_layer`` helpers), the
auto-activation path doesn't fire. Enable it yourself:

.. code-block:: python

   client = TileClient('path/to/geo.tif')
   client.enable_jupyter_loopback()

Or at the package level, which is handy when the port is known but the
client object isn't nearby:

.. code-block:: python

   import localtileserver

   localtileserver.enable_jupyter_loopback(port)

Both calls are idempotent -- registering the same port multiple times
is a no-op, so dropping :meth:`TileClient.enable_jupyter_loopback` into
a template or helper function is safe.

Opting out
----------

In JupyterLab / Hub / Binder / Notebook 7, the comm bridge is extra
machinery you don't need; it's cheap but not free (one anywidget
renders at the top of the cell where the tile layer is created). To
disable the auto-activation globally, set an environment variable
before importing ``localtileserver``:

.. code-block:: bash

   export LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK=1

Accepted truthy values are anything other than ``""``, ``0``, ``false``,
``no``, or ``off`` (case-insensitive).

Troubleshooting
---------------

Tiles still failing to load in VS Code Jupyter? Open the webview
devtools (``Developer: Open Webview Developer Tools`` in the command
palette) and check the console:

* ``window.__jupyter_loopback__`` should be defined. If not, the
  anywidget half of the bridge hasn't booted. In VS Code this is often
  because the extension's ipywidgets machinery can't reach
  ``unpkg.com`` for widget scripts; set ``jupyter.widgetScriptSources``
  in VS Code settings, or install ``ipywidgets`` into the kernel
  environment so VS Code uses the local copy.
* Look for ``jupyter_loopback.interceptLocalhost: image fetch failed``
  error lines -- they indicate a specific tile couldn't be fetched
  through the comm bridge. The cause is usually a tile-server crash
  upstream, not the bridge itself.
* ``http://127.0.0.1:<port>/…`` requests with ``net::ERR_FAILED``
  responses mean the interceptor wasn't installed for that port. Call
  :func:`localtileserver.enable_jupyter_loopback` with the port or
  invoke :meth:`TileClient.enable_jupyter_loopback` on the owning
  client.
