import os


def get_default_port():
    port = 0
    if "LOCALTILESERVER_PORT" in os.environ:
        port = int(os.environ["LOCALTILESERVER_PORT"])
    return port
