"""
Tests for :mod:`localtileserver._jupyter_loopback_bridge`.

These tests focus on the small surface the helper exposes -- the
env-var opt-out, idempotency, graceful behaviour when
``jupyter_loopback`` is old or incomplete -- without needing a full
Jupyter kernel or an active comm channel.
"""

from collections.abc import Iterator
import logging
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from localtileserver import _jupyter_loopback_bridge as bridge_mod
from localtileserver._jupyter_loopback_bridge import (
    _INTERCEPTED,
    enable_for_port,
    enable_jupyter_loopback,
)


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    """
    Clear per-kernel caches and the opt-out env var between tests.

    Without this, assertions about ``enable_comm_bridge`` call counts
    and one-shot warning flags leak across tests and cause order-
    dependent failures.
    """
    _INTERCEPTED.clear()
    bridge_mod._warned_old_version = False
    bridge_mod._warned_missing_extra = False
    saved = os.environ.pop("LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK", None)
    yield
    _INTERCEPTED.clear()
    bridge_mod._warned_old_version = False
    bridge_mod._warned_missing_extra = False
    if saved is not None:
        os.environ["LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK"] = saved
    else:
        os.environ.pop("LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK", None)


def _fake_jl(**attrs: Any) -> MagicMock:
    """
    Build a ``MagicMock`` shaped like ``jupyter_loopback`` with the
    right attributes present so ``hasattr`` / method calls behave.
    """
    fake = MagicMock()
    fake.__version__ = attrs.pop("version", "0.2.0")
    fake.is_comm_bridge_enabled.return_value = attrs.pop("enabled", False)
    for name, value in attrs.items():
        setattr(fake, name, value)
    return fake


def test_none_port_is_noop() -> None:
    """A ``None`` port must never touch jupyter_loopback."""
    fake = _fake_jl()
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_for_port(None)
    fake.enable_comm_bridge.assert_not_called()
    fake.intercept_localhost.assert_not_called()


def test_env_var_disables_activation() -> None:
    os.environ["LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK"] = "1"
    fake = _fake_jl()
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_for_port(12345)
    fake.enable_comm_bridge.assert_not_called()
    fake.intercept_localhost.assert_not_called()


@pytest.mark.parametrize("falsy", ["0", "false", "False", "NO", "off", ""])
def test_env_var_falsy_values_do_not_disable(falsy: str) -> None:
    """Opt-out is strict: only explicit truthy values turn it off."""
    if falsy:
        os.environ["LOCALTILESERVER_DISABLE_JUPYTER_LOOPBACK"] = falsy
    fake = _fake_jl()
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_for_port(9999)
    fake.enable_comm_bridge.assert_called_once()
    fake.intercept_localhost.assert_called_once_with(9999)


def test_old_jupyter_loopback_warns_once(caplog: pytest.LogCaptureFixture) -> None:
    """
    A pre-0.2 ``jupyter_loopback`` install lacks ``intercept_localhost``
    entirely. Surface it once at WARNING level so the user gets an
    actionable hint rather than silently failing tiles.
    """
    fake = MagicMock(spec=["__version__", "is_comm_bridge_enabled", "enable_comm_bridge"])
    fake.__version__ = "0.1.0"
    # ``hasattr(fake, "intercept_localhost")`` is False because ``spec=``
    # constrains the mock's attribute surface.
    with (
        patch.object(bridge_mod, "jupyter_loopback", fake),
        caplog.at_level(logging.WARNING, logger="localtileserver._jupyter_loopback_bridge"),
    ):
        enable_for_port(1234)
        enable_for_port(5678)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "intercept_localhost" in warnings[0].getMessage()
    assert "0.1.0" in warnings[0].getMessage()


def test_missing_comm_extra_warns_once(caplog: pytest.LogCaptureFixture) -> None:
    """
    When ``enable_comm_bridge`` raises ``ImportError`` (the ``[comm]``
    extra / ``anywidget`` is missing), emit one clear WARNING rather
    than swallowing silently.
    """
    fake = _fake_jl()
    fake.enable_comm_bridge.side_effect = ImportError("anywidget not installed")
    with (
        patch.object(bridge_mod, "jupyter_loopback", fake),
        caplog.at_level(logging.WARNING, logger="localtileserver._jupyter_loopback_bridge"),
    ):
        enable_for_port(7777)
        enable_for_port(8888)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "anywidget" in warnings[0].getMessage() or "comm extra" in warnings[0].getMessage()


def test_enable_comm_bridge_called_only_once_across_ports() -> None:
    """
    The bridge itself is singleton; repeated calls for distinct ports
    must each install the per-port interceptor but not re-display the
    bridge widget.
    """
    fake = _fake_jl()
    enabled_state = {"on": False}

    def fake_enable() -> None:
        enabled_state["on"] = True

    fake.is_comm_bridge_enabled.side_effect = lambda: enabled_state["on"]
    fake.enable_comm_bridge.side_effect = fake_enable
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_for_port(1111)
        enable_for_port(2222)
    assert fake.enable_comm_bridge.call_count == 1
    intercepted = [c.args[0] for c in fake.intercept_localhost.call_args_list]
    assert intercepted == [1111, 2222]


def test_repeat_same_port_is_idempotent() -> None:
    """Re-registering the same port must not re-emit the JS shim."""
    fake = _fake_jl(enabled=True)
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_for_port(5555)
        enable_for_port(5555)
        enable_for_port(5555)
    assert fake.intercept_localhost.call_count == 1


def test_public_alias_delegates_to_enable_for_port() -> None:
    """``enable_jupyter_loopback`` is the documented entry point."""
    fake = _fake_jl()
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_jupyter_loopback(4242)
    fake.intercept_localhost.assert_called_once_with(4242)


def test_bridge_exception_does_not_propagate() -> None:
    """
    ``enable_for_port`` is called from tile-layer construction and must
    never break that flow; if the bridge raises a non-ImportError, we
    swallow and debug-log.
    """
    fake = _fake_jl()
    fake.enable_comm_bridge.side_effect = RuntimeError("no frontend")
    with patch.object(bridge_mod, "jupyter_loopback", fake):
        enable_for_port(7777)  # must not raise
    assert 7777 not in _INTERCEPTED
