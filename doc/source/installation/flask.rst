🧬 Flask Blueprint
------------------

Under the hood, ``localtileserver`` is a basic Flask Blueprint that can be easily
incorporated into any Flask application. To utilize in your own application:

.. code:: python

  from flask import Flask
  from localtileserver.tileserver.blueprint import cache, tileserver

  app = Flask(__name__)
  cache.init_app(app)
  app.register_blueprint(tileserver, url_prefix='/')


.. note::

  There is an example Flask application and deployment in
  `banesullivan/remotetileserver <https://github.com/banesullivan/remotetileserver>`_
