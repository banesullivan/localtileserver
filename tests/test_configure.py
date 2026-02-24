"""Tests for localtileserver.configure."""

import os

from localtileserver.configure import get_default_client_params


def test_defaults_no_env():
    """Default values when no env vars are set."""
    # Remove any existing env vars
    env_keys = [
        "LOCALTILESERVER_CLIENT_HOST",
        "LOCALTILESERVER_CLIENT_PORT",
        "LOCALTILESERVER_CLIENT_PREFIX",
    ]
    saved = {}
    for k in env_keys:
        if k in os.environ:
            saved[k] = os.environ.pop(k)
    try:
        host, port, prefix = get_default_client_params()
        assert host is None
        assert port is None
        assert prefix is None
    finally:
        os.environ.update(saved)


def test_env_host():
    """LOCALTILESERVER_CLIENT_HOST env var."""
    os.environ["LOCALTILESERVER_CLIENT_HOST"] = "my-host.example.com"
    try:
        host, _port, _prefix = get_default_client_params()
        assert host == "my-host.example.com"
    finally:
        del os.environ["LOCALTILESERVER_CLIENT_HOST"]


def test_env_port():
    """LOCALTILESERVER_CLIENT_PORT env var."""
    os.environ["LOCALTILESERVER_CLIENT_PORT"] = "9999"
    try:
        _host, port, _prefix = get_default_client_params()
        assert port == 9999
    finally:
        del os.environ["LOCALTILESERVER_CLIENT_PORT"]


def test_env_prefix():
    """LOCALTILESERVER_CLIENT_PREFIX env var."""
    os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = "/proxy/{port}"
    try:
        _host, _port, prefix = get_default_client_params()
        assert prefix == "/proxy/{port}"
    finally:
        del os.environ["LOCALTILESERVER_CLIENT_PREFIX"]


def test_explicit_overrides_env():
    """Explicit args take precedence over env vars."""
    os.environ["LOCALTILESERVER_CLIENT_HOST"] = "env-host"
    os.environ["LOCALTILESERVER_CLIENT_PORT"] = "1111"
    os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = "/env"
    try:
        host, port, prefix = get_default_client_params(
            host="explicit-host", port=2222, prefix="/explicit"
        )
        assert host == "explicit-host"
        assert port == 2222
        assert prefix == "/explicit"
    finally:
        del os.environ["LOCALTILESERVER_CLIENT_HOST"]
        del os.environ["LOCALTILESERVER_CLIENT_PORT"]
        del os.environ["LOCALTILESERVER_CLIENT_PREFIX"]


def test_empty_env_vars_ignored():
    """Empty string env vars should be ignored."""
    os.environ["LOCALTILESERVER_CLIENT_HOST"] = ""
    try:
        host, _port, _prefix = get_default_client_params()
        assert host is None
    finally:
        del os.environ["LOCALTILESERVER_CLIENT_HOST"]
