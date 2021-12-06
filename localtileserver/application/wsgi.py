import logging

from localtileserver.application import app

if __name__ == "__main__":

    logging.getLogger("werkzeug").setLevel(logging.DEBUG)
    logging.getLogger("gdal").setLevel(logging.DEBUG)
    logging.getLogger("large_image").setLevel(logging.DEBUG)
    logging.getLogger("large_image_source_gdal").setLevel(logging.DEBUG)

    app.run()
