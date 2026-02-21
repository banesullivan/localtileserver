"""ASGI application entry point.

Used by uvicorn (e.g., ``uvicorn localtileserver.web.wsgi:app``).
"""

from localtileserver.web import create_app

app = create_app()
