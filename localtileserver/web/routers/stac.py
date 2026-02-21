"""STAC API endpoints for localtileserver."""

from fastapi import APIRouter, HTTPException, Query, Response
from rio_tiler.errors import TileOutsideBounds

from localtileserver.tiler import format_to_encoding
from localtileserver.tiler.stac import (
    get_stac_info,
    get_stac_preview,
    get_stac_reader,
    get_stac_statistics,
    get_stac_tile,
)

router = APIRouter(prefix="/api/stac", tags=["stac"])


def _parse_assets(assets: str | None) -> list[str] | None:
    if not assets:
        return None
    return [a.strip() for a in assets.split(",")]


@router.get("/info")
async def stac_info_view(
    url: str = Query(..., description="STAC item URL"),
    assets: str | None = Query(None, description="Comma-separated asset names"),
):
    try:
        reader = get_stac_reader(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read STAC item: {e}")
    return get_stac_info(reader, assets=_parse_assets(assets))


@router.get("/statistics")
async def stac_statistics_view(
    url: str = Query(..., description="STAC item URL"),
    assets: str | None = Query(None, description="Comma-separated asset names"),
):
    try:
        reader = get_stac_reader(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read STAC item: {e}")
    return get_stac_statistics(reader, assets=_parse_assets(assets))


@router.get("/tiles/{z}/{x}/{y}.{format}")
async def stac_tile_view(
    z: int,
    x: int,
    y: int,
    format: str,
    url: str = Query(..., description="STAC item URL"),
    assets: str | None = Query(None, description="Comma-separated asset names"),
    expression: str | None = Query(None),
):
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not valid.")
    try:
        reader = get_stac_reader(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read STAC item: {e}")
    try:
        tile_data = get_stac_tile(
            reader, z, x, y,
            assets=_parse_assets(assets),
            expression=expression,
            img_format=encoding,
        )
    except TileOutsideBounds:
        raise HTTPException(status_code=404, detail="Tile outside bounds")
    return Response(content=bytes(tile_data), media_type=f"image/{format.lower()}")


@router.get("/thumbnail.{format}")
async def stac_thumbnail_view(
    format: str,
    url: str = Query(..., description="STAC item URL"),
    assets: str | None = Query(None, description="Comma-separated asset names"),
    expression: str | None = Query(None),
    max_size: int = Query(512),
):
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format {format} is not valid.")
    try:
        reader = get_stac_reader(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read STAC item: {e}")
    thumb = get_stac_preview(
        reader,
        assets=_parse_assets(assets),
        expression=expression,
        img_format=encoding,
        max_size=max_size,
    )
    return Response(content=bytes(thumb), media_type=f"image/{format.lower()}")
