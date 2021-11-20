import logging
import pathlib
import threading
from werkzeug.serving import make_server


def get_app(path: pathlib.Path):
    from tileserver.application import app

    path = pathlib.Path(path).expanduser()
    app.config["path"] = path
    return app


def run_app(path: pathlib.Path, port: int = 0):
    app = get_app(path)
    return app.run(host="localhost", port=port)


class ServerThread(threading.Thread):
    def __init__(self, app, port=0):
        threading.Thread.__init__(self)
        self.srv = make_server("localhost", port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

    def __del__(self):
        self.shutdown()
        super().__del__()


def run_app_threaded(path: pathlib.Path, port: int = 0):
    app = get_app(path)

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    server = ServerThread(app)
    server.start()
    return server


class TileServer:
    def __init__(self, path: pathlib.Path, port: int = 0):
        self._path = path
        self._server = run_app_threaded(self._path, port)
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
