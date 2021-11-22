import logging
import pathlib
import requests
import threading
from werkzeug.serving import make_server

from tileserver.utilities import save_file_from_request
from tileserver.application.paths import inject_path, pop_path


def run_app(path: pathlib.Path, port: int = 0, debug: bool = False):
    from tileserver.application import app

    path = pathlib.Path(path).expanduser()
    inject_path("default", path)
    app.config["DEBUG"] = debug
    return app.run(host="localhost", port=port)


class TileServerThred(threading.Thread):
    """This is for internal use only."""

    def __init__(self, path: pathlib.Path, port: int = 0, debug: bool = False):
        threading.Thread.__init__(self)
        path = pathlib.Path(path).expanduser()

        from tileserver.application import app

        if not debug:
            logging.getLogger("werkzeug").setLevel(logging.ERROR)
            logging.getLogger("gdal").setLevel(logging.ERROR)
            logging.getLogger("large_image").setLevel(logging.ERROR)
        else:
            app.config["DEBUG"] = True

        self.daemon = True  # CRITICAL for safe exit
        self.srv = make_server("localhost", port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.path = path

    def run(self):
        # This is absolutely critical this happens here
        inject_path(self.ident, self.path)
        self.srv.serve_forever()

    def shutdown(self):
        if self.is_alive():
            self.srv.shutdown()
            pop_path(self.ident)

    def __del__(self):
        self.shutdown()


class TileServer:
    """Serve tiles from a local raster file in a background thread.

    Parameters
    ----------
    path : pathlib.Path
        The path on disk to use as the source raster for the tiles.
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.

    """

    def __init__(self, path: pathlib.Path, port: int = 0, debug: bool = False):
        self._server = TileServerThred(path, port, debug)
        self._server.start()  # run app threaded
        # Be careful if assigning any other attributes to avoid cycilical refs

    def __del__(self):
        self.shutdown()

    @property
    def server(self):
        return self._server

    @property
    def path(self):
        return self.server.path

    @property
    def port(self):
        return self.server.srv.port

    @property
    def base_url(self):
        return f"http://{self.server.srv.host}:{self.port}"

    def shutdown(self):
        self.server.shutdown()

    def create_url(self, path: str):
        return f"{self.base_url}/{path.lstrip('/')}"

    def get_tile_url(self, projection: str = "EPSG:3857"):
        url = self.create_url(f"tiles/{{z}}/{{x}}/{{y}}.png?")
        if projection:
            url += f"projection={projection}"
        return url

    def extract_roi(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        units: str = "EPSG:4326",
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
    ):
        """Extract ROI in world coordinates."""
        path = f"/region/world/{left}/{right}/{bottom}/{top}/region.tif?units={units}&encoding={encoding}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        return save_file_from_request(r, output_path)

    def extract_roi_pixel(
        self,
        left: int,
        right: int,
        bottom: int,
        top: int,
        encoding: str = "TILED",
        output_path: pathlib.Path = None,
    ):
        """Extract ROI in world coordinates."""
        path = f"/region/pixel/{left}/{right}/{bottom}/{top}/region.tif?encoding={encoding}"
        r = requests.get(self.create_url(path))
        r.raise_for_status()
        return save_file_from_request(r, output_path)

    def metadata(self):
        r = requests.get(self.create_url("/metadata"))
        r.raise_for_status()
        return r.json()

    def bounds(self, projection: str = "EPSG:4326"):
        """Get bounds in form of (ymin, ymax, xmin, xmax)."""
        r = requests.get(self.create_url(f"/bounds?projection={projection}"))
        r.raise_for_status()
        bounds = r.json()
        return (bounds["ymin"], bounds["ymax"], bounds["xmin"], bounds["xmax"])

    def center(self, projection: str = "EPSG:4326"):
        """Get center in the form of (y <lat>, x <lon>)."""
        bounds = self.bounds(projection=projection)
        return (
            (bounds[1] - bounds[0]) / 2 + bounds[0],
            (bounds[3] - bounds[2]) / 2 + bounds[2],
        )
