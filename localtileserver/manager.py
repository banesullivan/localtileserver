from localtileserver.web import create_app


class AppManager:
    _APP = None
    _RASTERIO_ENV = {}

    def __init__(self):
        raise NotImplementedError(
            "The ServerManager class cannot be instantiated."
        )  # pragma: no cover

    @staticmethod
    def get_or_create_app(cors_all: bool = False):
        if not AppManager._APP:
            AppManager._APP = create_app(cors_all=cors_all)
        return AppManager._APP

    @staticmethod
    def set_rasterio_env(env_dict: dict):
        """Store rasterio/GDAL environment options to forward to tile server threads."""
        AppManager._RASTERIO_ENV = dict(env_dict)

    @staticmethod
    def get_rasterio_env() -> dict:
        """Get stored rasterio/GDAL environment options."""
        return dict(AppManager._RASTERIO_ENV)
