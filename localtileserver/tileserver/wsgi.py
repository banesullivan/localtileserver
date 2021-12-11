import logging

from localtileserver.tileserver import create_app

logging.getLogger("werkzeug").setLevel(logging.DEBUG)
logging.getLogger("gdal").setLevel(logging.DEBUG)
logging.getLogger("large_image").setLevel(logging.DEBUG)
logging.getLogger("large_image_source_gdal").setLevel(logging.DEBUG)

app = create_app()
