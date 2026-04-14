# Import as run_app for entry_point
from localtileserver.web.fastapi_app import click_run_app as run_app

if __name__ == "__main__":  # pragma: no cover
    run_app()
