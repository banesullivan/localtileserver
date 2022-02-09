⬇️ Installation
===============

.. toctree::
   :hidden:

   remote-jupyter
   flask


Get started with ``localtileserver`` to view rasters locally in Jupyter or
deploy in your own Flask application.


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


If you prefer pip, and know how to install GDAL on your system, then you can
install from PyPI: https://pypi.org/project/localtileserver/

.. code:: bash

   pip install localtileserver ipyleaflet


📝 A Brief Note on Installing GDAL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GDAL can be a pain in the 🍑 to install, so you may want to handle GDAL
before installing ``localtileserver`` when using ``pip``.

If on linux, I highly recommend using the `large_image_wheels <https://github.com/girder/large_image_wheels>`_ from Kitware.

.. code:: bash

   pip install --find-links=https://girder.github.io/large_image_wheels --no-cache GDAL
