import os


def get_default_client_params(host: str = None, port: int = None, prefix: str = None):
    if (
        host is None
        and "LOCALTILESERVER_CLIENT_HOST" in os.environ
        and os.environ["LOCALTILESERVER_CLIENT_HOST"]
    ):
        host = str(os.environ["LOCALTILESERVER_CLIENT_HOST"])
    if (
        port is None
        and "LOCALTILESERVER_CLIENT_PORT" in os.environ
        and os.environ["LOCALTILESERVER_CLIENT_PORT"]
    ):
        port = int(os.environ["LOCALTILESERVER_CLIENT_PORT"])
    if (
        prefix is None
        and "LOCALTILESERVER_CLIENT_PREFIX" in os.environ
        and os.environ["LOCALTILESERVER_CLIENT_PREFIX"]
    ):
        prefix = str(os.environ["LOCALTILESERVER_CLIENT_PREFIX"])
    return host, port, prefix
