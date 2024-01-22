import logging

from localtileserver.web import create_app

logging.getLogger("werkzeug").setLevel(logging.DEBUG)
logging.getLogger("rasterio").setLevel(logging.DEBUG)
logging.getLogger("rio_tiler").setLevel(logging.DEBUG)

app = create_app()
