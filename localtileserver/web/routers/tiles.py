"""Tile and image-related API endpoints."""

# All endpoints that perform blocking GDAL/rasterio I/O are defined as
# regular ``def`` (not ``async def``) so that FastAPI runs them in a
# thread pool.  This keeps the event loop responsive and avoids broken
# request handling with Starlette's ``BaseHTTPMiddleware``.

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query, Request, Response
from rasterio import RasterioIOError
from rio_tiler.errors import TileOutsideBounds

from localtileserver.tiler import (
    format_to_encoding,
    get_meta_data,
    get_preview,
    get_reader,
    get_source_bounds,
    get_statistics,
    get_tile,
)
from localtileserver.tiler.data import get_sf_bay_url
from localtileserver.tiler.handler import get_feature, get_part
from localtileserver.tiler.palettes import get_palettes
from localtileserver.tiler.utilities import get_clean_filename
from localtileserver.web.routers.utils import parse_style_params

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tiles"])


@router.get("/palettes")
async def list_palettes():
    """Return the dictionary of available color palettes."""
    return get_palettes()


@router.get("/metadata")
def metadata_view(request: Request, filename: str = Query(None)):
    """Return raster metadata for the given file."""
    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    meta = get_meta_data(reader)
    meta["filename"] = filename
    return meta


@router.get("/bounds")
def bounds_view(
    request: Request,
    filename: str = Query(None),
    crs: str = Query("EPSG:4326"),
):
    """Return the geographic bounds of the raster."""
    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    bounds = get_source_bounds(reader, projection=crs)
    bounds["filename"] = filename
    return bounds


@router.get("/validate")
def validate_cog_view(request: Request, filename: str = Query(None)):
    """Validate whether the raster is a Cloud Optimized GeoTIFF."""
    # Deferred import: validate → client → manager → web → tiles (circular).
    from localtileserver.validate import validate_cog

    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    valid = validate_cog(reader, strict=True)
    if not valid:
        raise HTTPException(status_code=415, detail="Not a valid Cloud Optimized GeoTiff.")
    return "Valid Cloud Optimized GeoTiff."


@router.get("/statistics")
def statistics_view(
    request: Request,
    filename: str = Query(None),
    indexes: str | None = Query(None),
    expression: str | None = Query(None),
):
    """Return band statistics for the raster."""
    filename = _resolve_filename(request, filename)
    reader = _get_reader(filename)
    style = parse_style_params(indexes=indexes)
    return get_statistics(reader, expression=expression, **style)


@router.get("/thumbnail.{format}")
def thumbnail_view(
    request: Request,
    format: str,
    filename: str = Query(None),
    indexes: str | None = Query(None),
    colormap: str | None = Query(None),
    vmin: str | None = Query(None),
    vmax: str | None = Query(None),
    nodata: str | None = Query(None),
    crs: str | None = Query(None),
    expression: str | None = Query(None),
    stretch: str | None = Query(None),
):
    """Return a thumbnail preview image of the raster."""
    filename = _resolve_filename(request, filename)
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Format {format} is not a valid encoding."
        ) from None
    try:
        reader = _get_reader(filename)
        style = parse_style_params(
            indexes=indexes, colormap=colormap, vmin=vmin, vmax=vmax, nodata=nodata
        )
        thumb_data = get_preview(
            reader, img_format=encoding, crs=crs, expression=expression, stretch=stretch, **style
        )
    except RasterioIOError as e:
        logger.error("RasterioIOError rendering thumbnail: %s", e)
        raise HTTPException(status_code=500, detail=f"Rasterio error: {e}") from None
    except Exception as e:
        logger.error("Unexpected error rendering thumbnail: %s", e)
        raise HTTPException(status_code=500, detail=f"Thumbnail rendering error: {e}") from None
    return Response(content=bytes(thumb_data), media_type=f"image/{format.lower()}")


@router.get("/tiles/{z}/{x}/{y}.{format}")
def tile_view(
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
    expression: str | None = Query(None),
    stretch: str | None = Query(None),
):
    """Return a single map tile at the given z/x/y coordinates."""
    filename = _resolve_filename(request, filename)
    try:
        reader = _get_reader(filename)
        img_format = format_to_encoding(format)
        style = parse_style_params(
            indexes=indexes, colormap=colormap, vmin=vmin, vmax=vmax, nodata=nodata
        )
        tile_binary = get_tile(
            reader, z, x, y, img_format=img_format, expression=expression, stretch=stretch, **style
        )
    except TileOutsideBounds:
        raise HTTPException(status_code=404, detail="Tile outside bounds") from None
    except RasterioIOError as e:
        logger.error("RasterioIOError rendering tile z=%s x=%s y=%s: %s", z, x, y, e)
        raise HTTPException(status_code=500, detail=f"Rasterio error: {e}") from None
    except Exception as e:
        logger.error("Unexpected error rendering tile z=%s x=%s y=%s: %s", z, x, y, e)
        raise HTTPException(status_code=500, detail=f"Tile rendering error: {e}") from None
    return Response(content=bytes(tile_binary), media_type=f"image/{img_format.lower()}")


@router.get("/part.{format}")
def part_view(
    request: Request,
    format: str,
    bbox: str = Query(..., description="Bounding box as left,bottom,right,top"),
    filename: str = Query(None),
    indexes: str | None = Query(None),
    colormap: str | None = Query(None),
    vmin: str | None = Query(None),
    vmax: str | None = Query(None),
    nodata: str | None = Query(None),
    expression: str | None = Query(None),
    stretch: str | None = Query(None),
    max_size: int = Query(1024),
    dst_crs: str | None = Query(None),
    bounds_crs: str | None = Query(None),
):
    """Return a cropped image of the raster for the given bounding box."""
    filename = _resolve_filename(request, filename)
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Format {format} is not a valid encoding."
        ) from None
    try:
        parts = [float(x.strip()) for x in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError
        bbox_tuple = tuple(parts)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="bbox must be 4 comma-separated floats: left,bottom,right,top"
        ) from None
    try:
        reader = _get_reader(filename)
        style = parse_style_params(
            indexes=indexes, colormap=colormap, vmin=vmin, vmax=vmax, nodata=nodata
        )
        result = get_part(
            reader,
            bbox_tuple,
            img_format=encoding,
            max_size=max_size,
            dst_crs=dst_crs,
            bounds_crs=bounds_crs,
            expression=expression,
            stretch=stretch,
            **style,
        )
    except RasterioIOError as e:
        logger.error("RasterioIOError rendering part: %s", e)
        raise HTTPException(status_code=500, detail=f"Rasterio error: {e}") from None
    except Exception as e:
        logger.error("Unexpected error rendering part: %s", e)
        raise HTTPException(status_code=500, detail=f"Part rendering error: {e}") from None
    return Response(content=bytes(result), media_type=f"image/{format.lower()}")


@router.post("/feature.{format}")
def feature_view(
    request: Request,
    format: str,
    geojson: Annotated[dict, Body()],
    filename: str = Query(None),
    indexes: str | None = Query(None),
    colormap: str | None = Query(None),
    vmin: str | None = Query(None),
    vmax: str | None = Query(None),
    nodata: str | None = Query(None),
    expression: str | None = Query(None),
    stretch: str | None = Query(None),
    max_size: int = Query(1024),
    dst_crs: str | None = Query(None),
):
    """Return a cropped image of the raster clipped to a GeoJSON feature."""
    filename = _resolve_filename(request, filename)
    try:
        encoding = format_to_encoding(format)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Format {format} is not a valid encoding."
        ) from None
    try:
        reader = _get_reader(filename)
        style = parse_style_params(
            indexes=indexes, colormap=colormap, vmin=vmin, vmax=vmax, nodata=nodata
        )
        result = get_feature(
            reader,
            geojson,
            img_format=encoding,
            max_size=max_size,
            dst_crs=dst_crs,
            expression=expression,
            stretch=stretch,
            **style,
        )
    except RasterioIOError as e:
        logger.error("RasterioIOError rendering feature: %s", e)
        raise HTTPException(status_code=500, detail=f"Rasterio error: {e}") from None
    except Exception as e:
        logger.error("Unexpected error rendering feature: %s", e)
        raise HTTPException(status_code=500, detail=f"Feature rendering error: {e}") from None
    return Response(content=bytes(result), media_type=f"image/{format.lower()}")


def _resolve_filename(request: Request, filename: str | None) -> str:
    """Resolve the filename from query params, app state, or default."""
    if filename:
        return filename
    # Fallback to app.state.filename (set when running standalone server)
    app_filename = str(getattr(request.app.state, "filename", ""))
    if app_filename:
        return app_filename
    # Final fallback to sample data
    return get_sf_bay_url()


def _get_reader(filename: str):
    """Resolve filename and return a rio-tiler Reader."""
    try:
        clean = get_clean_filename(filename)
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        return get_reader(clean)
    except RasterioIOError as e:
        raise HTTPException(status_code=400, detail=f"RasterioIOError: {e!s}") from e
