import logging
import pathlib
import threading
from typing import Union

import requests
from werkzeug.serving import make_server

from localtileserver.client import BaseTileClient, RemoteTileClient

_LIVE_SERVERS = {}


logger = logging.getLogger(__name__)


class TileServerThread(threading.Thread):
    """This is for internal use only."""

    class ServerDownError(Exception):
        """Raised when a TileServerThread is down."""

        pass

    def __init__(
        self,
        port: int = 0,
        debug: bool = False,
        start: bool = True,
        threaded: bool = True,
        processes: int = 1,
    ):
        if not isinstance(port, int):
            raise ValueError(f"Port must be an int, not {type(port)}")
        if threaded and processes > 1:
            threaded = False

        threading.Thread.__init__(self)

        from localtileserver.application import app

        if not debug:
            logging.getLogger("werkzeug").setLevel(logging.ERROR)
            logging.getLogger("gdal").setLevel(logging.ERROR)
            logging.getLogger("large_image").setLevel(logging.ERROR)
        else:
            app.config["DEBUG"] = True
            logging.getLogger("werkzeug").setLevel(logging.DEBUG)
            logging.getLogger("gdal").setLevel(logging.DEBUG)
            logging.getLogger("large_image").setLevel(logging.DEBUG)
            logging.getLogger("large_image_source_gdal").setLevel(logging.DEBUG)
            # make_server -> passthrough_errors ?

        self.daemon = True  # CRITICAL for safe exit
        self.srv = make_server("localhost", port, app, threaded=threaded, processes=processes)
        self.ctx = app.app_context()
        self.ctx.push()
        if start:
            self.start()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        if self.is_alive():
            self.srv.shutdown()

    def __del__(self):
        self.shutdown()

    @property
    def port(self):
        return self.srv.port

    @property
    def host(self):
        return self.srv.host


def is_server_live(key: Union[int, str]):
    return key in _LIVE_SERVERS and _LIVE_SERVERS[key].is_alive()


def launch_server(
    port: Union[int, str] = "default",
    debug: bool = False,
    threaded: bool = True,
    processes: int = 1,
):
    if is_server_live(port):
        return port
    if port == "default":
        server = TileServerThread(0, debug, threaded=threaded, processes=processes)
    else:
        server = TileServerThread(port, debug, threaded=threaded, processes=processes)
        if port == 0:
            # Get reallocated port
            port = server.port
    _LIVE_SERVERS[port] = server
    return port


def shutdown_server(key: int, force: bool = False):
    if not force and key == "default":
        # We do not shut down the default server
        return
    try:
        server = _LIVE_SERVERS.pop(key)
        server.shutdown()
        del server
    except KeyError:
        logger.error(f"Server for key ({key}) not found.")


class TileClient(BaseTileClient):
    """Serve tiles from a local raster file in a background thread.

    Parameters
    ----------
    path : pathlib.Path, str
        The path on disk to use as the source raster for the tiles.
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.
    threaded : bool
        Run the background server as a ThreadedWSGIServer. Default True.
    processes : int
        If processes is greater than 1, run background server as ForkingWSGIServer

    """

    def __init__(
        self,
        filename: Union[pathlib.Path, str],
        port: Union[int, str] = "default",
        debug: bool = False,
        threaded: bool = True,
        processes: int = 1,
    ):
        super().__init__(filename)
        self._key = launch_server(port, debug, threaded=threaded, processes=processes)
        # Store actual port just in case
        self._port = _LIVE_SERVERS[self._key].srv.port

    def __del__(self):
        self.shutdown()

    @property
    def server(self):
        try:
            return _LIVE_SERVERS[self._key]
        except KeyError:
            raise TileServerThread.ServerDownError("Tile server for this source has been shutdown.")

    @property
    def port(self):
        return self.server.port

    @property
    def host(self):
        return self.server.host

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

    def shutdown(self, force: bool = False):
        shutdown_server(self._key, force=force)


def get_or_create_tile_client(
    source: Union[pathlib.Path, str, TileClient],
    port: Union[int, str] = "default",
    debug: bool = False,
):
    """A helper to safely get a TileClient from a path on disk.

    To Do
    -----
    There should eventually be a check to see if a TileClient instance exists
    for the given filename. For now, it is not really a big deal because the
    default is for all TileClient's to share a single server.

    """
    if isinstance(source, RemoteTileClient):
        return source, False
    _internally_created = False
    # Launch tile server if file path is given
    if not isinstance(source, TileClient):
        source = TileClient(source, port, debug)
        _internally_created = True
    # Check that the tile source is valid and no server errors
    try:
        r = requests.get(source.create_url("metadata"))
        r.raise_for_status()
    except requests.HTTPError as e:
        # Make sure to destroy the server and its thread if internally created.
        if _internally_created:
            source.shutdown()
            del source
        raise e
    return source, _internally_created
