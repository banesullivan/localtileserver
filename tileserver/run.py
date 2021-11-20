import pathlib
import socket


def get_free_port():
    try:
        s = socket.socket()  # create a socket object
        s.bind(("localhost", 0))  # Bind to the port
        port = s.getsockname()[1]
        s.close()
        return port
    except OSError:
        pass
    raise OSError("All ports are in use")


def run_app(path: pathlib.Path, port: int = 0):
    from .application import app

    app.config["path"] = path
    app.run(host="localhost", port=port)
    return app
