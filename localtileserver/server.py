import logging
import os
import threading
from typing import Union

from werkzeug.serving import make_server

logger = logging.getLogger(__name__)


class ServerDownError(Exception):
    """Raised when a TileServerThread is down."""

    pass


class ServerManager:
    _LIVE_SERVERS = {}
    _APP = None

    def __init__(self):
        raise NotImplementedError("The ServerManager class cannot be instantiated.")

    @staticmethod
    def get_or_create_app():
        from localtileserver.tileserver import create_app

        if not ServerManager._APP:
            ServerManager._APP = create_app()
        return ServerManager._APP

    @staticmethod
    def server_count():
        return len(ServerManager._LIVE_SERVERS)

    @staticmethod
    def is_server_live(key: Union[int, str]):
        return key in ServerManager._LIVE_SERVERS and ServerManager._LIVE_SERVERS[key].is_alive()

    @staticmethod
    def add_server(key, val):
        ServerManager._LIVE_SERVERS[key] = val

    @staticmethod
    def pop_server(key):
        try:
            return ServerManager._LIVE_SERVERS.pop(key)
        except KeyError:
            raise ServerDownError("Tile server for this source has been shutdown.")

    @staticmethod
    def get_server(key):
        try:
            return ServerManager._LIVE_SERVERS[key]
        except KeyError:
            raise ServerDownError("Tile server for this source has been shutdown.")

    @staticmethod
    def shutdown_server(key: int, force: bool = False):
        if not force and key == "default":
            # We do not shut down the default server
            return
        try:
            server = ServerManager.pop_server(key)
            server.shutdown()
            del server
        except ServerDownError:
            logger.error(f"Server for key ({key}) not found.")


class TileServerThread(threading.Thread):
    """This is for internal use only."""

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
        if processes > 1 and not hasattr(os, "fork"):
            logger.error("Your platform does not support forking. Failing to multithreading.")
            processes = 1
            threaded = True
        if threaded and processes > 1:
            threaded = False

        threading.Thread.__init__(self)

        app = ServerManager.get_or_create_app()

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


def launch_server(
    port: Union[int, str] = "default",
    debug: bool = False,
    threaded: bool = True,
    processes: int = 1,
):
    if ServerManager.is_server_live(port):
        return port
    if port == "default":
        server = TileServerThread(0, debug, threaded=threaded, processes=processes)
    else:
        server = TileServerThread(port, debug, threaded=threaded, processes=processes)
        if port == 0:
            # Get reallocated port
            port = server.port
    ServerManager.add_server(port, server)
    return port
