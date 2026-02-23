"""Test concurrent tile requests mimicking browser map loads.

When a Leaflet/ipyleaflet map loads, the browser fires many tile
requests simultaneously.  These tests verify that the tile server
handles this correctly without returning 500 errors.
"""

import concurrent.futures

from morecantile import tms
import requests

# Valid tiles for bahamas_rgb.tif at zoom 7 (matches the user-reported errors)
BAHAMAS_TILES_Z7 = [
    (7, 35, 54),
    (7, 36, 54),
    (7, 35, 55),
    (7, 36, 55),
]

# Valid tiles for bahamas_rgb.tif at zoom 8
BAHAMAS_TILES_Z8 = [
    (8, 71, 109),
    (8, 72, 109),
    (8, 73, 109),
    (8, 71, 110),
    (8, 72, 110),
    (8, 73, 110),
]


def _fetch_tile(url):
    """Fetch a single tile and return (url, status_code, content_length)."""
    r = requests.get(url, timeout=10)
    return url, r.status_code, len(r.content)


def test_concurrent_tile_requests_bahamas(bahamas):
    """Fire all z7 + z8 tiles at once, like a browser would."""
    tile_url_template = bahamas.get_tile_url()
    urls = []
    for z, x, y in BAHAMAS_TILES_Z7 + BAHAMAS_TILES_Z8:
        urls.append(tile_url_template.format(z=z, x=x, y=y))

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:
        futures = [pool.submit(_fetch_tile, url) for url in urls]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    failures = [(url, status) for url, status, _ in results if status != 200]
    assert not failures, f"Tile requests failed: {failures}"
    # Verify all returned actual image data
    for url, _status, length in results:
        assert length > 0, f"Empty tile response from {url}"


def test_repeated_concurrent_tile_bursts_bahamas(bahamas):
    """Simulate multiple rapid pan/zoom events (several bursts)."""
    tile_url_template = bahamas.get_tile_url()
    urls = [tile_url_template.format(z=z, x=x, y=y) for z, x, y in BAHAMAS_TILES_Z7]

    for burst in range(5):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:
            futures = [pool.submit(_fetch_tile, url) for url in urls]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        failures = [(url, status) for url, status, _ in results if status != 200]
        assert not failures, f"Burst {burst}: tile requests failed: {failures}"


def test_concurrent_tile_requests_landsat(landsat7):
    """Same test with a different (larger, multi-band) raster."""
    tile_url_template = landsat7.get_tile_url()
    # Fetch a grid of tiles at the default zoom
    z = landsat7.default_zoom
    # bounds() returns (south, north, west, east)
    south, north, west, east = landsat7.bounds()

    grid = tms.get("WebMercatorQuad")
    tiles = list(grid.tiles(west, south, east, north, zooms=z))

    urls = [tile_url_template.format(z=t.z, x=t.x, y=t.y) for t in tiles[:20]]

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as pool:
        futures = [pool.submit(_fetch_tile, url) for url in urls]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    failures = [(url, status) for url, status, _ in results if status != 200]
    assert not failures, f"Tile requests failed: {failures}"
