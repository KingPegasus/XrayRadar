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


def test_admin_emails_parsed_from_env(monkeypatch):
    """ADMIN_EMAILS is parsed from XRAYRADAR_ADMIN_EMAILS (comma-separated, trimmed, lowercased, deduped)."""
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", " admin@test.com , b@Example.COM , admin@test.com ")
    if "xrayradar_server.constants" in sys.modules:
        del sys.modules["xrayradar_server.constants"]
    import xrayradar_server.constants as constants_mod
    importlib.reload(constants_mod)
    assert constants_mod.ADMIN_EMAILS == ["admin@test.com", "b@example.com"]


def test_max_signups_per_day_from_env(monkeypatch):
    """MAX_SIGNUPS_PER_DAY is read from env; default 100; 0 = no limit; invalid falls back to 100."""
    monkeypatch.setenv("XRAYRADAR_MAX_SIGNUPS_PER_DAY", "50")
    if "xrayradar_server.constants" in sys.modules:
        del sys.modules["xrayradar_server.constants"]
    import xrayradar_server.constants as constants_mod
    importlib.reload(constants_mod)
    assert constants_mod.MAX_SIGNUPS_PER_DAY == 50

    monkeypatch.setenv("XRAYRADAR_MAX_SIGNUPS_PER_DAY", "0")
    if "xrayradar_server.constants" in sys.modules:
        del sys.modules["xrayradar_server.constants"]
    import xrayradar_server.constants as constants_mod0
    importlib.reload(constants_mod0)
    assert constants_mod0.MAX_SIGNUPS_PER_DAY == 0

    monkeypatch.setenv("XRAYRADAR_MAX_SIGNUPS_PER_DAY", "not_an_int")
    if "xrayradar_server.constants" in sys.modules:
        del sys.modules["xrayradar_server.constants"]
    import xrayradar_server.constants as constants_mod2
    importlib.reload(constants_mod2)
    assert constants_mod2.MAX_SIGNUPS_PER_DAY == 100


def test_admin_emails_empty_when_unset(monkeypatch):
    """ADMIN_EMAILS is empty list when XRAYRADAR_ADMIN_EMAILS is unset or empty."""
    monkeypatch.delenv("XRAYRADAR_ADMIN_EMAILS", raising=False)
    if "xrayradar_server.constants" in sys.modules:
        del sys.modules["xrayradar_server.constants"]
    import xrayradar_server.constants as constants_mod
    importlib.reload(constants_mod)
    assert constants_mod.ADMIN_EMAILS == []
