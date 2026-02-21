"""Mosaic API endpoints for localtileserver."""

from fastapi import APIRouter, HTTPException, Query, Request, Response
from rio_tiler.errors import TileOutsideBounds

from localtileserver.tiler import format_to_encoding
from localtileserver.tiler.mosaic import get_mosaic_preview, get_mosaic_tile

router = APIRouter(prefix="/api/mosaic", tags=["mosaic"])


def _parse_file_list(request: Request, files: str | None) -> list[str]:
    """Parse comma-separated file list or use app state."""
    if files:
        return [f.strip() for f in files.split(",") if f.strip()]
    # Fallback to app state
    mosaic_assets = getattr(request.app.state, "mosaic_assets", None)
    if mosaic_assets:
        return list(mosaic_assets)
    raise HTTPException(
        status_code=400,
        detail="Provide 'files' query parameter (comma-separated paths) or register mosaic_assets in app state.",
    )


@router.get("/tiles/{z}/{x}/{y}.{format}")
async def mosaic_tile_view(
    request: Request,
    z: int,
    x: int,
    y: int,
    format: str,
    files: str | None = Query(None, description="Comma-separated file paths or URLs"),
    indexes: str | None = Query(None),
):
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not valid.")
    assets = _parse_file_list(request, files)
    idx = None
    if indexes:
        idx = [int(i.strip()) for i in indexes.split(",")]
    try:
        tile_data = get_mosaic_tile(assets, z, x, y, img_format=encoding, indexes=idx)
    except TileOutsideBounds:
        raise HTTPException(status_code=404, detail="Tile outside bounds")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=bytes(tile_data), media_type=f"image/{format.lower()}")


@router.get("/thumbnail.{format}")
async def mosaic_thumbnail_view(
    request: Request,
    format: str,
    files: str | None = Query(None, description="Comma-separated file paths or URLs"),
    indexes: str | None = Query(None),
    max_size: int = Query(512),
):
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not valid.")
    assets = _parse_file_list(request, files)
    idx = None
    if indexes:
        idx = [int(i.strip()) for i in indexes.split(",")]
    try:
        thumb = get_mosaic_preview(assets, img_format=encoding, max_size=max_size, indexes=idx)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=bytes(thumb), media_type=f"image/{format.lower()}")
