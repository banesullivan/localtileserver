"""
Tests for localtileserver's Jupyter Server extension.

The proxy handler, URL autodetect, and end-to-end cross-process
behavior are all tested in the ``jupyter-loopback`` package. This file
only tests the plumbing localtileserver owns:

1. The extension declares itself correctly so ``jupyter server
   extension list`` finds it.
2. The extension's load hook mounts the loopback proxy for the
   ``localtileserver`` namespace on the web_app.
3. ``get_default_client_params`` delegates to
   :func:`jupyter_loopback.autodetect_prefix` under the same env-var
   conditions, and user env-var overrides win over autodetect.
4. The ``jupyter-config`` JSON that auto-enables the extension on
   install is present on disk.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from localtileserver import _jupyter
from localtileserver.configure import get_default_client_params


def test_jupyter_server_extension_points() -> None:
    points = _jupyter._jupyter_server_extension_points()
    assert points == [{"module": "localtileserver._jupyter"}]


def test_extension_mounts_localtileserver_namespace_proxy() -> None:
    """The load hook registers ``/localtileserver-proxy/...`` on the web_app."""
    from jupyter_loopback._server import _REGISTERED
    from tornado.web import Application

    _REGISTERED.clear()
    app = Application([], base_url="/", cookie_secret="x")
    fake_log = SimpleNamespace(info=lambda *a, **kw: None)
    fake_server_app = SimpleNamespace(web_app=app, log=fake_log)

    _jupyter._load_jupyter_server_extension(fake_server_app)

    patterns: list[str] = []
    for outer in app.default_router.rules:
        target = outer.target
        if hasattr(target, "rules"):
            for inner in target.rules:
                regex = getattr(inner.matcher, "regex", None)
                if regex is not None:
                    patterns.append(regex.pattern)
    # ``re.escape`` escapes the hyphen, so the stored pattern is
    # ``localtileserver\\-proxy``. Match on the unambiguous suffix.
    assert any("tileserver-proxy" in p for p in patterns), patterns


def test_jupyter_config_json_shipped() -> None:
    """Auto-enable config exists for the jupyter-server extension system."""
    config_path = (
        Path(__file__).resolve().parents[1]
        / "jupyter-config"
        / "jupyter_server_config.d"
        / "localtileserver.json"
    )
    assert config_path.exists()
    body = json.loads(config_path.read_text())
    assert body["ServerApp"]["jpserver_extensions"]["localtileserver._jupyter"] is True


# ---------------------------------------------------------------------------
# Autodetect delegation
# ---------------------------------------------------------------------------


_JUPYTER_ENV_VARS = (
    "JPY_SESSION_NAME",
    "JPY_PARENT_PID",
    "JUPYTERHUB_SERVICE_PREFIX",
    "JPY_BASE_URL",
    "LOCALTILESERVER_CLIENT_HOST",
    "LOCALTILESERVER_CLIENT_PORT",
    "LOCALTILESERVER_CLIENT_PREFIX",
)


def _clear(monkeypatch) -> None:
    for var in _JUPYTER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_autodetect_noop_without_jupyter_env(monkeypatch) -> None:
    _clear(monkeypatch)
    assert get_default_client_params() == (None, None, None)


def test_autodetect_returns_localtileserver_prefix(monkeypatch) -> None:
    """Inside a Jupyter kernel, autodetect yields the localtileserver namespace."""
    _clear(monkeypatch)
    monkeypatch.setenv("JPY_SESSION_NAME", "nb.ipynb")
    host, port, prefix = get_default_client_params()
    assert host is None
    assert port is None
    assert prefix == "/localtileserver-proxy/{port}"


def test_autodetect_prepends_hub_prefix(monkeypatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("JPY_SESSION_NAME", "nb.ipynb")
    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/alice/")
    _, _, prefix = get_default_client_params()
    assert prefix == "/user/alice/localtileserver-proxy/{port}"


def test_env_prefix_overrides_autodetect(monkeypatch) -> None:
    """User-set env vars still win over autodetect."""
    monkeypatch.setenv("JPY_SESSION_NAME", "nb.ipynb")
    monkeypatch.setenv("LOCALTILESERVER_CLIENT_PREFIX", "custom/{port}")
    _, _, prefix = get_default_client_params()
    assert prefix == "custom/{port}"


def test_explicit_host_disables_autodetect(monkeypatch) -> None:
    """Passing ``host=`` explicitly also suppresses the prefix autodetect."""
    monkeypatch.setenv("JPY_SESSION_NAME", "nb.ipynb")
    host, _port, prefix = get_default_client_params(host="example.com")
    assert host == "example.com"
    assert prefix is None
