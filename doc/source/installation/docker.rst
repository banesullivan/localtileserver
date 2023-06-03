.. _docker:

🐳 Docker
---------

Included in this repository's packages is a pre-built Docker image that can be
used as a local tile serving service. To use, pull the image and run it by
mounting your local volume where the imagery is stored and forward port 8000.

This is particularly useful if you do not want to install the dependencies on
your system or want a dedicated and isolated service for tile serving.

To use the docker image:

.. code:: bash

  docker pull ghcr.io/banesullivan/localtileserver:latest
  docker run -p 8000:8000 ghcr.io/banesullivan/localtileserver:latest


Then visit http://localhost:8000 in your browser. You can pass the `?filename=`
argument in the URL parameters to access any URL/S3 raster image file.

You can mount your local file system to access files on your filesystem. For
example, mount your Desktop by:

.. code:: bash

  docker run -p 8000:8000 -v /Users/bane/Desktop/:/data/ ghcr.io/banesullivan/localtileserver:latest


Then add the `?filename=` parameter to the URL in your browser to access the
local files. Since this is mounted under `/data/` in the container, you must
build the path as `/data/<filename on Desktop>`, such that the URL would be:
http://localhost:8000/?filename=/data/TC_NG_SFBay_US_Geo.tif

.. note::

  Check out the container on GitHub's package registry: https://github.com/banesullivan/localtileserver/pkgs/container/localtileserver


.. _jupyter-docker:

📓 Jupyter in Docker
~~~~~~~~~~~~~~~~~~~~

There is also a pre-built image with localtileserver configured to be used in
Jupyer from a Docker container.

.. code:: bash

  docker run -p 8888:8888 ghcr.io/banesullivan/localtileserver-jupyter:latest


.. note::

  Check out the container on GitHub's package registry: https://github.com/banesullivan/localtileserver/pkgs/container/localtileserver-jupyter
