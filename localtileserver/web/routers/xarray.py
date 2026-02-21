"""Xarray API endpoints for localtileserver."""

from fastapi import APIRouter, HTTPException, Query, Request, Response
from rio_tiler.errors import TileOutsideBounds

from localtileserver.tiler import format_to_encoding
from localtileserver.tiler.xarray_handler import (
    _check_xarray,
    get_xarray_info,
    get_xarray_preview,
    get_xarray_statistics,
    get_xarray_tile,
)

router = APIRouter(prefix="/api/xarray", tags=["xarray"])


def _get_xarray_reader(request: Request, key: str | None = None):
    """Retrieve a registered XarrayReader from app state.

    Xarray DataArrays are registered in-memory by the client, so they
    cannot be passed as URLs.  Instead, clients call
    ``app.state.xarray_registry[key] = reader`` and pass the key in
    the query string.
    """
    _check_xarray()
    registry = getattr(request.app.state, "xarray_registry", None)
    if registry is None:
        raise HTTPException(status_code=400, detail="No xarray datasets registered.")
    if key is None:
        # If only one dataset registered, use it
        if len(registry) == 1:
            return next(iter(registry.values()))
        raise HTTPException(
            status_code=400,
            detail="Multiple xarray datasets registered; specify 'key' parameter.",
        )
    if key not in registry:
        raise HTTPException(status_code=404, detail=f"Xarray dataset '{key}' not found.")
    return registry[key]


@router.get("/info")
async def xarray_info_view(
    request: Request,
    key: str | None = Query(None, description="Registry key for the xarray dataset"),
):
    """Return metadata for a registered xarray dataset."""
    reader = _get_xarray_reader(request, key)
    return get_xarray_info(reader)


@router.get("/statistics")
async def xarray_statistics_view(
    request: Request,
    key: str | None = Query(None, description="Registry key for the xarray dataset"),
    indexes: str | None = Query(None),
):
    """Return band statistics for a registered xarray dataset."""
    reader = _get_xarray_reader(request, key)
    idx = None
    if indexes:
        idx = [int(i.strip()) for i in indexes.split(",")]
    return get_xarray_statistics(reader, indexes=idx)


@router.get("/tiles/{z}/{x}/{y}.{format}")
async def xarray_tile_view(
    request: Request,
    z: int,
    x: int,
    y: int,
    format: str,
    key: str | None = Query(None, description="Registry key for the xarray dataset"),
    indexes: str | None = Query(None),
):
    """Return a single map tile for a registered xarray dataset."""
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not valid.") from None
    reader = _get_xarray_reader(request, key)
    idx = None
    if indexes:
        idx = [int(i.strip()) for i in indexes.split(",")]
    try:
        tile_data = get_xarray_tile(reader, z, x, y, img_format=encoding, indexes=idx)
    except TileOutsideBounds:
        raise HTTPException(status_code=404, detail="Tile outside bounds") from None
    return Response(content=bytes(tile_data), media_type=f"image/{format.lower()}")


@router.get("/thumbnail.{format}")
async def xarray_thumbnail_view(
    request: Request,
    format: str,
    key: str | None = Query(None, description="Registry key for the xarray dataset"),
    indexes: str | None = Query(None),
    max_size: int = Query(512),
):
    """Return a thumbnail preview image for a registered xarray dataset."""
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not valid.") from None
    reader = _get_xarray_reader(request, key)
    idx = None
    if indexes:
        idx = [int(i.strip()) for i in indexes.split(",")]
    thumb = get_xarray_preview(reader, img_format=encoding, max_size=max_size, indexes=idx)
    return Response(content=bytes(thumb), media_type=f"image/{format.lower()}")
