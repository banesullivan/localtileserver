import os


def get_default_port():
    port = 0
    if "LOCALTILESERVER_PORT" in os.environ:
        port = int(os.environ["LOCALTILESERVER_PORT"])
    return port


def get_default_client_params(host: str = None, port: int = None, prefix: str = None):
    if host is None and "LOCALTILESERVER_CLIENT_HOST" in os.environ:
        host = str(os.environ["LOCALTILESERVER_CLIENT_HOST"])
    if port is None and "LOCALTILESERVER_CLIENT_PORT" in os.environ:
        port = int(os.environ["LOCALTILESERVER_CLIENT_PORT"])
    if prefix is None and "LOCALTILESERVER_CLIENT_PREFIX" in os.environ:
        prefix = str(os.environ["LOCALTILESERVER_CLIENT_PREFIX"])
    return host, port, prefix
