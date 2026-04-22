📡 Remote Jupyter
-----------------

``localtileserver`` works in remote Jupyter environments (JupyterHub,
MyBinder, JupyterLab behind HTTPS) with zero user configuration.
Installing ``localtileserver[jupyter]`` pulls in
`jupyter-loopback <https://github.com/banesullivan/jupyter-loopback>`_,
which ships a tiny ``jupyter-server`` extension that proxies
``<base_url>/localtileserver-proxy/<port>/...`` to the in-kernel tile
server, plus a kernel-side autodetect that routes URLs through that
prefix automatically.

.. code:: bash

    pip install localtileserver[jupyter]

Create ``TileClient`` instances the same way you would locally.
``get_leaflet_tile_layer`` and ``get_folium_tile_layer`` produce URLs
that resolve through the proxy on Lab, Hub, and Binder alike. The Hub
per-user prefix (``/user/<name>/``) is handled automatically.


Manual prefix override
~~~~~~~~~~~~~~~~~~~~~~

If you're routing through something other than the bundled extension
(for example an existing ``jupyter-server-proxy`` setup), set
``LOCALTILESERVER_CLIENT_PREFIX`` and the autodetect stays out of the
way:

.. code::

   export LOCALTILESERVER_CLIENT_PREFIX='proxy/{port}'


Frontends without a Jupyter server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

VS Code Remote notebooks, Google Colab, Shiny for Python, Solara, and
marimo don't run a ``jupyter-server``, so the HTTP proxy above isn't
available. ``jupyter-loopback`` ships a ``anywidget`` comm bridge for
these cases; it's not wired into ``localtileserver`` yet. Watch for
follow-up work or use the manual override above to point at whatever
proxy your environment provides.
