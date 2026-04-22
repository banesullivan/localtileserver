"""
Singleton application manager for the shared FastAPI tile server.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from fastapi import FastAPI

from localtileserver.web import create_app


class AppManager:
    """
    Singleton manager for the shared FastAPI tile-serving application.
    """

    _APP: ClassVar[FastAPI | None] = None

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
        Forward rasterio/GDAL environment options to the tile server.

        Sets each option as a process-level environment variable so that
        GDAL picks them up from any thread (including the background
        tile-server thread).

        Parameters
        ----------
        env_dict : dict
            Dictionary of rasterio/GDAL environment options.
        """
        for key, value in env_dict.items():
            os.environ[str(key)] = str(value)
