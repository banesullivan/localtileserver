"""Tile and image-related API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request, Response
from rasterio import RasterioIOError
from rio_tiler.errors import TileOutsideBounds

from localtileserver.tiler import (
    format_to_encoding,
    get_meta_data,
    get_preview,
    get_reader,
    get_source_bounds,
    get_tile,
)
from localtileserver.tiler.palettes import get_palettes
from localtileserver.web.routers.utils import get_clean_filename_from_params, parse_style_params

router = APIRouter(prefix="/api", tags=["tiles"])


@router.get("/palettes")
async def list_palettes():
    return get_palettes()


@router.get("/metadata")
async def metadata_view(request: Request, filename: str = Query(None)):
    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    meta = get_meta_data(reader)
    meta["filename"] = filename
    return meta


@router.get("/bounds")
async def bounds_view(
    request: Request,
    filename: str = Query(None),
    crs: str = Query("EPSG:4326"),
):
    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    bounds = get_source_bounds(reader, projection=crs)
    bounds["filename"] = filename
    return bounds


@router.get("/validate")
async def validate_cog_view(request: Request, filename: str = Query(None)):
    from localtileserver.validate import validate_cog

    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    valid = validate_cog(reader, strict=True)
    if not valid:
        raise HTTPException(status_code=415, detail="Not a valid Cloud Optimized GeoTiff.")
    return "Valid Cloud Optimized GeoTiff."


@router.get("/thumbnail.{format}")
async def thumbnail_view(
    request: Request,
    format: str,
    filename: str = Query(None),
    indexes: str | None = Query(None),
    colormap: str | None = Query(None),
    vmin: str | None = Query(None),
    vmax: str | None = Query(None),
    nodata: str | None = Query(None),
    crs: str | None = Query(None),
):
    filename = _resolve_filename(request, filename)
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not a valid encoding.")
    reader = _get_reader(filename)
    style = parse_style_params(indexes=indexes, colormap=colormap, vmin=vmin, vmax=vmax, nodata=nodata)
    thumb_data = get_preview(reader, img_format=encoding, crs=crs, **style)
    return Response(content=bytes(thumb_data), media_type=f"image/{format.lower()}")


@router.get("/tiles/{z}/{x}/{y}.{format}")
async def tile_view(
    request: Request,
    z: int,
    x: int,
    y: int,
    format: str,
    filename: str = Query(None),
    indexes: str | None = Query(None),
    colormap: str | None = Query(None),
    vmin: str | None = Query(None),
    vmax: str | None = Query(None),
    nodata: str | None = Query(None),
):
    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    img_format = format_to_encoding(format)
    style = parse_style_params(indexes=indexes, colormap=colormap, vmin=vmin, vmax=vmax, nodata=nodata)
    try:
        tile_binary = get_tile(reader, z, x, y, img_format=img_format, **style)
    except TileOutsideBounds:
        raise HTTPException(status_code=404, detail="Tile outside bounds")
    return Response(content=bytes(tile_binary), media_type=f"image/{img_format.lower()}")


def _resolve_filename(request: Request, filename: str | None) -> str:
    """Resolve the filename from query params, app state, or default."""
    if filename:
        return filename
    # Fallback to app.state.filename (set when running standalone server)
    app_filename = str(getattr(request.app.state, "filename", ""))
    if app_filename:
        return app_filename
    # Final fallback to sample data
    from localtileserver.tiler.data import get_sf_bay_url

    return get_sf_bay_url()


def _get_reader(filename: str):
    """Resolve filename and return a rio-tiler Reader."""
    from localtileserver.tiler.utilities import get_clean_filename

    try:
        clean = get_clean_filename(filename)
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        return get_reader(clean)
    except RasterioIOError as e:
        raise HTTPException(status_code=400, detail=f"RasterioIOError: {e!s}")
