📡 Remote Jupyter
-----------------

``localtileserver`` is usable in remote Jupyter environments such JupyterHub
on services like MyBinder. Further, you may be running Jupyter in a Docker
container or other host and accessing through a browser on an arbitrary client.
In order to retrieve tiles into the ipyleaflet or folium Jupyter widgets
client-side in the browser, we must make sure the port on which
``localtileserver`` is serving tiles is accessible to your browser.

To make this easy, we can levarage `jupyter-server-proxy <https://github.com/jupyterhub/jupyter-server-proxy>`_ to expose the port on the Jupyter server through a proxy URL.

Steps to use ``localtileserver`` in remote Jupyter environments:

1. Install ``jupyter-server-proxy`` for JupyterLab >= 3

.. code::

   pip install jupyter-server-proxy

2. Set ``LOCALTILESERVER_CLIENT_PREFIX`` in your environment to ``'proxy/{port}'`` (stop here in most cases, continue to 3. if using JupyterHub):

.. code::

  export LOCALTILESERVER_CLIENT_PREFIX='proxy/{port}'

3. If using JupyterHub, you may need to alter ``LOCALTILESERVER_CLIENT_PREFIX`` such that it includes your users ID. For example, on MyBinder, we are required to do:

.. code:: python

  # Set host forwarding for MyBinder
  import os
  os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f"{os.environ['JUPYTERHUB_SERVICE_PREFIX']}/proxy/{{port}}"


.. note::

  For more context, check out :ref:`jupyter-docker`
