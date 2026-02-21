"""FastAPI application factory for localtileserver."""

import logging
import os
import pathlib
import socket
import threading
import webbrowser

import click
import rasterio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from localtileserver.tiler import get_clean_filename
from localtileserver.web.routers.tiles import router as tiles_router

logger = logging.getLogger(__name__)

_WEB_DIR = pathlib.Path(__file__).parent
_TEMPLATE_DIR = _WEB_DIR / "templates"
_STATIC_DIR = _WEB_DIR / "static"


def create_app(
    url_prefix: str = "/",
    cors_all: bool = False,
    debug: bool = False,
    cesium_token: str = "",
):
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="localtileserver",
        docs_url="/swagger/",
        debug=debug,
    )

    # Store config values as app state
    app.state.cesium_token = cesium_token
    app.state.debug = debug

    if cors_all:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Mount static files
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Include API routers
    app.include_router(tiles_router)

    # Set up Jinja2 templates
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # Provide a Flask-compatible url_for in templates
    def _template_url_for(name: str, **kwargs) -> str:
        """Map Flask-style url_for names to FastAPI paths."""
        _ROUTE_MAP = {
            "tileserver.index": "/",
            "tileserver.split-form": "/split/form/",
            "tileserver.doc": "/swagger/",
        }
        if name == "tileserver.static" or name == "static":
            fn = kwargs.get("filename", "")
            return f"/static/{fn}"
        if name in _ROUTE_MAP:
            return _ROUTE_MAP[name]
        # Fallback: try FastAPI's own url_path_for
        try:
            return app.url_path_for(name, **kwargs)
        except Exception:
            return "/"

    templates.env.globals["url_for"] = _template_url_for

    # rasterio env middleware (#182)
    @app.middleware("http")
    async def rasterio_env_middleware(request: Request, call_next):
        from localtileserver.manager import AppManager

        rio_env = AppManager.get_rasterio_env()
        if rio_env:
            with rasterio.Env(**rio_env):
                response = await call_next(request)
        else:
            response = await call_next(request)
        return response

    # HTML view routes
    @app.get("/", response_class=HTMLResponse)
    async def cesium_viewer(request: Request, filename: str = ""):
        context = _build_template_context(request, app, filename, cesium_token)
        if "bounds" not in context:
            return templates.TemplateResponse(
                request, "tileserver/404file.html", context, status_code=404
            )
        return templates.TemplateResponse(request, "tileserver/cesiumViewer.html", context)

    @app.get("/split/", response_class=HTMLResponse)
    async def cesium_split_viewer(request: Request, filenameA: str = "", filenameB: str = ""):
        context = _build_template_context(request, app, filenameA, cesium_token)
        if "bounds" not in context:
            return templates.TemplateResponse(
                request, "tileserver/404file.html", context, status_code=404
            )
        return templates.TemplateResponse(request, "tileserver/cesiumSplitViewer.html", context)

    @app.get("/split/form/", response_class=HTMLResponse)
    async def split_form(request: Request):
        context = _build_template_context(request, app, "", cesium_token)
        return templates.TemplateResponse(request, "tileserver/splitForm.html", context)

    if debug:
        logging.getLogger("uvicorn").setLevel(logging.DEBUG)
        logging.getLogger("rasterio").setLevel(logging.DEBUG)
        logging.getLogger("rio_tiler").setLevel(logging.DEBUG)

    return app


def _build_template_context(
    request: Request, app: FastAPI, filename: str, cesium_token: str = ""
) -> dict:
    """Build the template rendering context."""
    from localtileserver.tiler import data
    from localtileserver.tiler.data import get_sf_bay_url
    from localtileserver.tiler.handler import get_meta_data, get_reader, get_source_bounds

    # Resolve filename: query param -> app.state.filename -> sf_bay fallback
    if not filename:
        filename = str(getattr(app.state, "filename", ""))
    if not filename:
        filename = get_sf_bay_url()

    context = {"request": request, "filename": filename}

    # Try to load raster metadata
    try:
        clean_name = get_clean_filename(filename)
        tile_source = get_reader(clean_name)
        context.update(get_meta_data(tile_source))
        context["bounds"] = get_source_bounds(tile_source, projection="EPSG:4326")
    except Exception:
        pass

    # Sample data context
    context["filename_dem"] = data.get_data_path("aws_elevation_tiles_prod.xml")
    context["filename_bluemarble"] = data.get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    context["filename_virtualearth"] = data.get_data_path("frmt_wms_virtualearth.xml")
    context["filename_sf_bay"] = data.get_sf_bay_url()
    context["filename_landsat_salt_lake"] = data.get_data_path("landsat.tif")
    context["filename_oam2"] = data.get_oam2_url()
    context["cesium_token"] = cesium_token

    # Google Analytics
    mid = os.environ.get("GOOGLE_ANALYTICS_MID", "")
    if mid:
        context["google_analytics_mid"] = mid

    return context


def run_app(
    filename,
    port: int = 0,
    debug: bool = False,
    browser: bool = True,
    cesium_token: str = "",
    host: str = "127.0.0.1",
    cors_all: bool = False,
    run: bool = True,
):
    """Serve tiles from the raster at ``filename``.

    You can also pass the name of one of the example datasets: ``elevation``,
    ``blue_marble``, ``virtual_earth``, ``arcgis`` or ``bahamas``.
    """
    import uvicorn

    filename = get_clean_filename(filename)
    if not str(filename).startswith("/vsi") and not filename.exists():
        raise OSError(f"File does not exist: {filename}")
    app = create_app(cors_all=cors_all, debug=debug, cesium_token=cesium_token)
    app.state.filename = filename
    if os.name == "nt" and host == "127.0.0.1":
        host = "localhost"
    if port == 0:
        sock = socket.socket()
        sock.bind((host, 0))
        port = sock.getsockname()[1]
        sock.close()
    if browser:
        url = f"http://{host}:{port}?filename={filename}"
        threading.Timer(1, lambda: webbrowser.open(url)).start()
    if run:
        uvicorn.run(app, host=host, port=port, log_level="debug" if debug else "error")
    return app


@click.command()
@click.argument("filename")
@click.option("-p", "--port", default=0)
@click.option("-d", "--debug", default=False)
@click.option("-b", "--browser", default=True)
@click.option("-t", "--cesium-token", default="")
@click.option("-h", "--host", default="127.0.0.1")
@click.option("-c", "--cors-all", default=False)
def click_run_app(*args, **kwargs):
    return run_app(*args, **kwargs)
