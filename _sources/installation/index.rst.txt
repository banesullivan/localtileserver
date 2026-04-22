⬇️ Installation
===============

.. toctree::
   :hidden:

   remote-jupyter
   docker


Get started with ``localtileserver`` to view rasters locally in Jupyter or
deploy as your own FastAPI application.


🐍 Installing with ``conda``
----------------------------

.. image:: https://img.shields.io/conda/vn/conda-forge/localtileserver.svg?logo=conda-forge&logoColor=white
   :target: https://anaconda.org/conda-forge/localtileserver
   :alt: conda-forge

Conda makes managing ``localtileserver``'s dependencies across platforms quite
easy and this is the recommended method to install:

.. code:: bash

   conda install -c conda-forge localtileserver ipyleaflet


🎡 Installing with ``pip``
--------------------------

.. image:: https://img.shields.io/pypi/v/localtileserver.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/localtileserver/
   :alt: PyPI


If you prefer pip, then you can install from PyPI: https://pypi.org/project/localtileserver/

.. code:: bash

   pip install localtileserver ipyleaflet


📦 Optional Dependencies
-------------------------

``localtileserver`` provides several optional dependency groups for extended functionality:

**Xarray/DataArray support** (NetCDF, Zarr tile serving):

.. code:: bash

   pip install localtileserver[xarray]

This installs ``xarray`` and ``rioxarray`` for serving tiles directly from
xarray DataArrays.

**Jupyter widget integration:**

.. code:: bash

   pip install localtileserver[jupyter]

This installs ``ipyleaflet`` for inline map rendering. The underlying
``jupyter-loopback`` proxy and comm bridge are already pulled in by the
core install, so tiles work out of the box in JupyterLab / Hub / Binder
as well as VS Code Jupyter, Google Colab, Shiny, Solara, and marimo.
See :doc:`remote-jupyter` and :ref:`webview-frontends` for details.

**Additional colormaps:**

.. code:: bash

   pip install localtileserver[colormaps]

This installs ``matplotlib``, ``cmocean``, and ``colorcet`` for a wide range
of scientific colormaps.

**Geometry helpers:**

.. code:: bash

   pip install localtileserver[helpers]

This installs ``shapely`` for geometry conversion utilities.
