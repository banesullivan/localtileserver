import logging
import pathlib
import threading
from werkzeug.serving import make_server

from tileserver.application.paths import inject_path


def run_app(path: pathlib.Path, port: int = 0, debug: bool = False):
    from tileserver.application import app

    path = pathlib.Path(path).expanduser()
    app.config["path"] = path
    app.config["DEBUG"] = debug
    return app.run(host="localhost", port=port)


class TileServerThred(threading.Thread):
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

    def __del__(self):
        self.shutdown()


class TileServer:
    def __init__(self, path: pathlib.Path, port: int = 0, debug: bool = False):
        self._path = pathlib.Path(path).expanduser()
        self._server = TileServerThred(self._path, port, debug)
        self._server.start()  # run app threaded
        self._port = self.server.srv.port

    @property
    def path(self):
        return self._path

    @property
    def port(self):
        return self._port

    @property
    def server(self):
        return self._server

    @property
    def base_url(self):
        return f"http://{self.server.srv.host}:{self.port}"

    def shutdown(self):
        self.server.shutdown()

    def create_url(self, path: str):
        return f"{self.base_url}/{path.lstrip('/')}"
