"""
Top-level entrypoint for opening a raster source as a tile client.
"""

from __future__ import annotations

import pathlib

import rasterio

from localtileserver.client import STACClient, TileClient, get_or_create_tile_client


def open(
    source: pathlib.Path | str | TileClient | STACClient | rasterio.io.DatasetReaderBase,
    port: int | str = "default",
    debug: bool = False,
    host: str = "127.0.0.1",
    client_port: int | None = None,
    client_host: str | None = None,
    client_prefix: str | None = None,
    cors_all: bool = False,
) -> TileClient | STACClient:
    """
    Open a raster source as a :class:`~localtileserver.TileClient`.

    Convenience entrypoint modeled after ``rasterio.open`` /
    ``xarray.open_dataset``. Launches a background tile server for the
    given source and returns a client ready for use with
    :func:`~localtileserver.get_leaflet_tile_layer`,
    :func:`~localtileserver.get_folium_tile_layer`, and the other
    visualization helpers.

    If ``source`` is already a :class:`~localtileserver.TileClient` or
    :class:`~localtileserver.STACClient`, it is validated and returned
    unchanged.

    Parameters
    ----------
    source : pathlib.Path, str, TileClient, STACClient, or rasterio.io.DatasetReaderBase
        The raster source. A local path, a URL to a remote COG, a
        :class:`rasterio.io.DatasetReader`, or an already-running client.
    port : int or str, optional
        Port on the host machine for the tile server. Defaults to
        ``"default"``, which picks an available port.
    debug : bool, optional
        Run the tile server in debug mode.
    host : str, optional
        Host address to bind the tile server to.
    client_port : int, optional
        Port the client browser should use when fetching tiles. Useful
        when running in Docker with port forwarding.
    client_host : str, optional
        Host the client browser should use when fetching tiles.
    client_prefix : str, optional
        URL prefix for proxied access to the tile server.
    cors_all : bool, optional
        If ``True``, enable CORS for all origins on the tile server.

    Returns
    -------
    TileClient or STACClient
        A running tile client for ``source``.

    Examples
    --------
    >>> import localtileserver as lts
    >>> client = lts.open("path/to/raster.tif")
    >>> client.default_zoom  # doctest: +SKIP
    """
    if isinstance(source, (TileClient, STACClient)):
        client, _ = get_or_create_tile_client(source)
        return client
    client = TileClient(
        source,
        port=port,
        debug=debug,
        host=host,
        client_port=client_port,
        client_host=client_host,
        client_prefix=client_prefix,
        cors_all=cors_all,
    )
    # Validate the server is responding (and clean up if not).
    client, _ = get_or_create_tile_client(client)
    return client
