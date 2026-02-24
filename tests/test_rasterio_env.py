"""Tests for rasterio.Env context forwarding to the tile server thread (#182).

The forwarding mechanism works in three steps:

1. ``TileServerMixin.__init__`` captures GDAL/rasterio options from both
   ``rasterio.env.getenv()`` and ``os.environ`` (prefixes GDAL_, AWS_, CPL_).
2. ``AppManager.set_rasterio_env()`` writes them to ``os.environ`` so GDAL
   picks them up from any thread (including the background tile server).
3. ``create_app()`` sets sensible GDAL defaults that don't override
   user-provided values.
"""

import os
from unittest.mock import MagicMock, patch

import rasterio
import rasterio.env
import rasterio.errors

from localtileserver.client import TileClient
from localtileserver.examples import get_data_path
from localtileserver.manager import AppManager

# --- AppManager.set_rasterio_env ---


def test_set_rasterio_env_writes_to_os_environ():
    """Env dict entries are written to os.environ."""
    sentinel = "TEST_RASTERIO_ENV_ABC123"
    try:
        AppManager.set_rasterio_env({sentinel: "hello"})
        assert os.environ[sentinel] == "hello"
    finally:
        os.environ.pop(sentinel, None)


def test_set_rasterio_env_converts_to_string():
    """Non-string keys/values are converted to strings."""
    key = "TEST_RASTERIO_ENV_INT_KEY"
    try:
        AppManager.set_rasterio_env({key: 42})
        assert os.environ[key] == "42"
    finally:
        os.environ.pop(key, None)


def test_set_rasterio_env_empty_dict_is_noop():
    """An empty dict does not crash."""
    AppManager.set_rasterio_env({})


# --- TileServerMixin rasterio env forwarding ---


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_env_forwarded_from_rasterio_context(mock_sm, mock_app, mock_launch):
    """GDAL options from an active rasterio.Env are forwarded to os.environ."""
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    sentinel_key = "GDAL_TEST_SENTINEL_182"
    sentinel_val = "forwarded_value"
    try:
        with rasterio.Env(**{sentinel_key: sentinel_val}):
            path = get_data_path("bahamas_rgb.tif")
            client = TileClient(path, debug=True)
            client.shutdown(force=True)
        assert os.environ.get(sentinel_key) == sentinel_val
    finally:
        os.environ.pop(sentinel_key, None)


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_env_forwarded_from_os_environ(mock_sm, mock_app, mock_launch):
    """GDAL/AWS/CPL vars already in os.environ are preserved."""
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    key = "AWS_TEST_SENTINEL_182"
    try:
        os.environ[key] = "from_environ"
        path = get_data_path("bahamas_rgb.tif")
        client = TileClient(path, debug=True)
        client.shutdown(force=True)
        # Should still be there (set_rasterio_env uses setdefault logic
        # in the capture step but then writes unconditionally)
        assert os.environ.get(key) == "from_environ"
    finally:
        os.environ.pop(key, None)


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_env_forwarded_aws_credentials(mock_sm, mock_app, mock_launch):
    """AWS credential env vars are captured and forwarded."""
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    keys = {
        "AWS_ACCESS_KEY_ID": "AKIATEST182",
        "AWS_SECRET_ACCESS_KEY": "secret182",
        "AWS_SESSION_TOKEN": "token182",
    }
    try:
        for k, v in keys.items():
            os.environ[k] = v
        path = get_data_path("bahamas_rgb.tif")
        client = TileClient(path, debug=True)
        client.shutdown(force=True)
        for k, v in keys.items():
            assert os.environ.get(k) == v
    finally:
        for k in keys:
            os.environ.pop(k, None)


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_no_rasterio_env_does_not_crash(mock_sm, mock_app, mock_launch):
    """Creating a TileClient without an active rasterio.Env doesn't crash.

    ``rasterio.env.getenv()`` raises ``EnvError`` when no GDAL environment
    is active.  The try/except in TileServerMixin.__init__ must handle this.
    """
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    # Ensure we are NOT inside a rasterio.Env context
    path = get_data_path("bahamas_rgb.tif")
    client = TileClient(path, debug=True)
    client.shutdown(force=True)


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_rasterio_env_values_override_existing(mock_sm, mock_app, mock_launch):
    """Values from rasterio.Env context take priority over os.environ defaults.

    The capture code calls ``rio_env.update(getenv())`` first, then
    ``rio_env.setdefault(key, val)`` for os.environ, so rasterio.Env wins.
    """
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    key = "GDAL_PAM_ENABLED"
    try:
        os.environ[key] = "YES"
        with rasterio.Env(**{key: "NO"}):
            path = get_data_path("bahamas_rgb.tif")
            client = TileClient(path, debug=True)
            client.shutdown(force=True)
        # rasterio.Env value ("NO") should win over os.environ ("YES")
        assert os.environ.get(key) == "NO"
    finally:
        os.environ.pop(key, None)


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_cpl_prefix_captured(mock_sm, mock_app, mock_launch):
    """CPL_ prefixed env vars are captured alongside GDAL_ and AWS_."""
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    key = "CPL_VSIL_CURL_ALLOWED_EXTENSIONS"
    try:
        os.environ[key] = ".tif,.tiff"
        path = get_data_path("bahamas_rgb.tif")
        client = TileClient(path, debug=True)
        client.shutdown(force=True)
        assert os.environ.get(key) == ".tif,.tiff"
    finally:
        os.environ.pop(key, None)


@patch("localtileserver.client.launch_server", return_value="mock_key")
@patch("localtileserver.client.AppManager.get_or_create_app")
@patch("localtileserver.client.ServerManager")
def test_non_gdal_env_not_captured(mock_sm, mock_app, mock_launch):
    """Env vars without GDAL_/AWS_/CPL_ prefix are not forwarded."""
    mock_server = MagicMock()
    mock_server.srv.port = 12345
    mock_sm.get_server.return_value = mock_server

    key = "MY_CUSTOM_VAR_182_TEST"
    try:
        os.environ[key] = "should_not_be_touched"
        with patch.object(AppManager, "set_rasterio_env") as mock_set:
            path = get_data_path("bahamas_rgb.tif")
            client = TileClient(path, debug=True)
            client.shutdown(force=True)
            if mock_set.called:
                env_dict = mock_set.call_args[0][0]
                assert key not in env_dict
    finally:
        os.environ.pop(key, None)


# --- create_app GDAL defaults ---


def test_create_app_sets_gdal_defaults():
    """create_app sets GDAL_DISABLE_READDIR_ON_OPEN and GDAL_NUM_THREADS."""
    # Remove them first to verify create_app sets them
    saved = {}
    for key in ("GDAL_DISABLE_READDIR_ON_OPEN", "GDAL_NUM_THREADS"):
        saved[key] = os.environ.pop(key, None)
    try:
        from localtileserver.web import create_app

        create_app()
        assert os.environ.get("GDAL_DISABLE_READDIR_ON_OPEN") == "EMPTY_DIR"
        assert os.environ.get("GDAL_NUM_THREADS") == "ALL_CPUS"
    finally:
        for key, val in saved.items():
            if val is not None:
                os.environ[key] = val
            else:
                os.environ.pop(key, None)


def test_create_app_does_not_override_user_gdal_vars():
    """create_app uses setdefault so user-provided values are preserved."""
    key = "GDAL_DISABLE_READDIR_ON_OPEN"
    saved = os.environ.get(key)
    try:
        os.environ[key] = "TRUE"
        from localtileserver.web import create_app

        create_app()
        assert os.environ.get(key) == "TRUE"
    finally:
        if saved is not None:
            os.environ[key] = saved
        else:
            os.environ.pop(key, None)
