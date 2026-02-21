"""
Singleton application manager for the shared FastAPI tile server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from fastapi import FastAPI

from localtileserver.web import create_app


class AppManager:
    """
    Singleton manager for the shared FastAPI tile-serving application.
    """

    _APP: ClassVar[FastAPI | None] = None
    _RASTERIO_ENV: ClassVar[dict] = {}

    def __init__(self):
        raise NotImplementedError(
            "The ServerManager class cannot be instantiated."
        )  # pragma: no cover

    @staticmethod
    def get_or_create_app(cors_all: bool = False):
        """
        Return the shared FastAPI app, creating it if necessary.

        Parameters
        ----------
        cors_all : bool, optional
            If ``True``, enable permissive CORS headers allowing all origins.

        Returns
        -------
        fastapi.FastAPI
            The singleton FastAPI application instance.
        """
        if not AppManager._APP:
            AppManager._APP = create_app(cors_all=cors_all)
        return AppManager._APP

    @staticmethod
    def set_rasterio_env(env_dict: dict):
        """
        Store rasterio/GDAL environment options to forward to tile server threads.

        Parameters
        ----------
        env_dict : dict
            Dictionary of rasterio/GDAL environment options.
        """
        AppManager._RASTERIO_ENV = dict(env_dict)

    @staticmethod
    def get_rasterio_env() -> dict:
        """
        Get stored rasterio/GDAL environment options.

        Returns
        -------
        dict
            Copy of the stored rasterio/GDAL environment options.
        """
        return dict(AppManager._RASTERIO_ENV)
