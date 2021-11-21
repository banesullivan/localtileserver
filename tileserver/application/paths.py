import pathlib
import threading

_THREAD_FILE_PATHS = {}


def inject_path(ident: int, path: pathlib.Path):
    _THREAD_FILE_PATHS[ident] = path


def get_path():
    """Get the path for the current thread."""
    try:
        return _THREAD_FILE_PATHS[threading.get_ident()]
    except KeyError:
        pass
    try:
        return _THREAD_FILE_PATHS["default"]
    except KeyError:
        raise KeyError(
            f"Current thread has no file path set. Thread ID: {threading.get_ident()}"
        )


def pop_path(ident: int = None):
    """Remove the path for this thread (cleanup routine)."""
    if ident is None:
        ident = threading.get_ident()
    return _THREAD_FILE_PATHS.pop(ident, None)
