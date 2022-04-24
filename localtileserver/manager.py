from localtileserver.tileserver import create_app


class AppManager:
    _APP = None

    def __init__(self):
        raise NotImplementedError(
            "The ServerManager class cannot be instantiated."
        )  # pragma: no cover

    @staticmethod
    def get_or_create_app():
        if not AppManager._APP:
            AppManager._APP = create_app()
        return AppManager._APP
