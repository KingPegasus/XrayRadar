"""Tests for constants module (env parsing, fallbacks)."""

import importlib
import sys

import pytest


def test_scheduler_interval_seconds_invalid_env_fallback(monkeypatch):
    """When XRAYRADAR_SCHEDULER_INTERVAL_SECONDS is not an int, fallback to 60."""
    monkeypatch.setenv("XRAYRADAR_SCHEDULER_INTERVAL_SECONDS", "not_an_int")
    if "xrayradar_server.constants" in sys.modules:
        del sys.modules["xrayradar_server.constants"]
    import xrayradar_server.constants as constants_mod
    importlib.reload(constants_mod)
    assert constants_mod.SCHEDULER_INTERVAL_SECONDS == 60
