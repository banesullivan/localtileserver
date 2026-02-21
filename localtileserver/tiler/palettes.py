import hashlib
import json
import logging
import threading

from rio_tiler.colormap import cmap as RIO_CMAPS

logger = logging.getLogger(__name__)

# Thread-safe server-side colormap registry for custom colormaps (#231).
# Keyed by content hash so that identical colormaps share the same entry.
_COLORMAP_REGISTRY: dict[str, dict] = {}
_REGISTRY_LOCK = threading.Lock()


def register_colormap(colormap_data: dict) -> str:
    """Register a custom colormap and return its hash key.

    Parameters
    ----------
    colormap_data : dict
        Colormap as {int: (r, g, b, a)} dict.

    Returns
    -------
    str
        Hash key for the registered colormap (e.g., ``"custom:abc123def456"``).

    """
    serialized = json.dumps(colormap_data, sort_keys=True)
    hash_key = hashlib.md5(serialized.encode()).hexdigest()[:12]
    with _REGISTRY_LOCK:
        _COLORMAP_REGISTRY[hash_key] = colormap_data
    return f"custom:{hash_key}"


def get_registered_colormap(key: str) -> dict | None:
    """Look up a registered colormap by its ``custom:<hash>`` key.

    Returns None if the key is not in the registry.
    """
    if not key.startswith("custom:"):
        return None
    hash_key = key[len("custom:"):]
    with _REGISTRY_LOCK:
        return _COLORMAP_REGISTRY.get(hash_key)


def is_rio_cmap(name: str):
    """Check whether cmap is supported by rio-tiler."""
    return name in RIO_CMAPS.data.keys()


def palette_valid_or_raise(name: str):
    if name.startswith("custom:"):
        if get_registered_colormap(name) is None:
            raise ValueError(f"Custom colormap not found in registry: {name}")
        return
    if not is_rio_cmap(name):
        raise ValueError(f"Please use a valid rio-tiler registered colormap name. Invalid: {name}")


def get_palettes():
    """List of available palettes."""
    return {"matplotlib": list(RIO_CMAPS.data.keys())}
