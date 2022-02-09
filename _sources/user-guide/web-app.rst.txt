🖥️ Local Web Application
------------------------

Launch the tileserver from the commandline to use the included web application where you can view the raster and extract regions of interest.

.. code:: bash

  python -m localtileserver path/to/raster.tif


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/cesium-viewer.png

You can use the web viewer to extract regions of interest:

.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/webviewer-roi.gif


You can also launch the web viewer with any of the available example datasets:

.. code:: bash

  python -m localtileserver dem


Available choices are:

- ``dem`` or ``elevation``: global elevation dataset
- ``blue_marble``: Blue Marble satellite imagery
- ``virtual_earth``: Microsoft's satellite/aerial imagery
- ``arcgis``: ArcGIS World Street Map
- ``bahamas``: Sample raster over the Bahamas
