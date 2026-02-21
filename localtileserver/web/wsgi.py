"""
ASGI application entry point.

Used by uvicorn (e.g., ``uvicorn localtileserver.web.wsgi:app``).
"""

import os

from localtileserver.tiler.data import str_to_bool
from localtileserver.web import create_app

cors_all = str_to_bool(os.environ.get("LOCALTILESERVER_CORS_ALL", "false"))
app = create_app(cors_all=cors_all)
