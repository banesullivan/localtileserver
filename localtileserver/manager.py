from localtileserver.web import create_app


class AppManager:
    _APP = None

    def __init__(self):
        raise NotImplementedError(
            "The ServerManager class cannot be instantiated."
        )  # pragma: no cover

    @staticmethod
    def get_or_create_app(cors_all: bool = False):
        if not AppManager._APP:
            AppManager._APP = create_app(cors_all=cors_all)
        return AppManager._APP
