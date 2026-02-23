"""
FastAPI application factory for localtileserver.
"""

import logging
import os
import pathlib
import socket
import threading
import webbrowser

import click
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from localtileserver.tiler import data as tiler_data, get_clean_filename
from localtileserver.tiler.data import get_sf_bay_url
from localtileserver.tiler.handler import get_meta_data, get_reader, get_source_bounds
from localtileserver.web.routers.mosaic import router as mosaic_router
from localtileserver.web.routers.stac import router as stac_router
from localtileserver.web.routers.tiles import router as tiles_router
from localtileserver.web.routers.xarray import router as xarray_router

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
    """
    Create and configure the FastAPI application.

    Parameters
    ----------
    url_prefix : str, optional
        URL prefix for the application routes. Default is ``"/"``.
    cors_all : bool, optional
        If ``True``, enable permissive CORS headers allowing all origins.
    debug : bool, optional
        Run the application in debug mode with verbose logging.
    cesium_token : str, optional
        Cesium Ion access token for the 3-D globe viewer.

    Returns
    -------
    fastapi.FastAPI
        The configured FastAPI application instance.
    """
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
    app.include_router(stac_router)
    app.include_router(xarray_router)
    app.include_router(mosaic_router)

    # Set up Jinja2 templates
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # Provide a Flask-compatible url_for in templates
    def _template_url_for(name: str, **kwargs) -> str:
        """
        Map Flask-style url_for names to FastAPI paths.
        """
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

    # GDAL/rasterio environment setup (#182).
    #
    # IMPORTANT: We intentionally do NOT use a per-request rasterio.Env()
    # middleware here.  rasterio.Env uses a thread-local stack, and with
    # async middleware the __enter__/__exit__ calls from concurrent
    # requests interleave on the same thread, causing the stack to be
    # popped in the wrong order:
    #
    #   Request A enters Env → stack [A]
    #   Request B enters Env → stack [A, B]
    #   Request A exits  Env → pops B (wrong!)
    #   Request B exits  Env → "No GDAL environment exists" → 500
    #
    # Instead, GDAL options are set once as process-level env vars.
    # User-provided options (e.g. AWS credentials forwarded from a
    # notebook) are also written to os.environ by
    # AppManager.set_rasterio_env() so GDAL picks them up from any
    # thread automatically.
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("GDAL_NUM_THREADS", "ALL_CPUS")

    # HTML view routes — use sync ``def`` because _build_template_context
    # does blocking rasterio I/O.
    @app.get("/", response_class=HTMLResponse)
    def cesium_viewer(request: Request, filename: str = ""):
        """
        Render the Cesium 3-D globe viewer page.
        """
        context = _build_template_context(request, app, filename, cesium_token)
        if "bounds" not in context:
            return templates.TemplateResponse(
                request, "tileserver/404file.html", context, status_code=404
            )
        return templates.TemplateResponse(request, "tileserver/cesiumViewer.html", context)

    @app.get("/split/", response_class=HTMLResponse)
    def cesium_split_viewer(request: Request, filenameA: str = "", filenameB: str = ""):
        """
        Render the Cesium split-view comparison page.
        """
        context = _build_template_context(request, app, filenameA, cesium_token)
        if "bounds" not in context:
            return templates.TemplateResponse(
                request, "tileserver/404file.html", context, status_code=404
            )
        return templates.TemplateResponse(request, "tileserver/cesiumSplitViewer.html", context)

    @app.get("/split/form/", response_class=HTMLResponse)
    def split_form(request: Request):
        """
        Render the split-view input form page.
        """
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
    """
    Build the template rendering context.
    """
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
    context["filename_dem"] = tiler_data.get_data_path("aws_elevation_tiles_prod.xml")
    context["filename_bluemarble"] = tiler_data.get_data_path("frmt_wms_bluemarble_s3_tms.xml")
    context["filename_virtualearth"] = tiler_data.get_data_path("frmt_wms_virtualearth.xml")
    context["filename_sf_bay"] = tiler_data.get_sf_bay_url()
    context["filename_landsat_salt_lake"] = tiler_data.get_data_path("landsat.tif")
    context["filename_oam2"] = tiler_data.get_oam2_url()
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
    """
    Serve tiles from the raster at ``filename``.

    You can also pass the name of one of the example datasets: ``elevation``,
    ``blue_marble``, ``virtual_earth``, ``arcgis`` or ``bahamas``.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to a raster file or the name of a built-in example dataset.
    port : int, optional
        Port to bind the server to. ``0`` (default) picks an available port.
    debug : bool, optional
        Run the server with verbose debug logging.
    browser : bool, optional
        Open a web browser pointing to the viewer on startup.
    cesium_token : str, optional
        Cesium Ion access token for the 3-D globe viewer.
    host : str, optional
        Hostname to bind the server to. Default is ``"127.0.0.1"``.
    cors_all : bool, optional
        If ``True``, enable permissive CORS headers allowing all origins.
    run : bool, optional
        If ``True`` (default), start the uvicorn server. If ``False``, return
        the app without running it.

    Returns
    -------
    fastapi.FastAPI
        The configured and (optionally running) FastAPI application.
    """
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
    """
    CLI entry point for serving tiles from a raster file.
    """
    return run_app(*args, **kwargs)
