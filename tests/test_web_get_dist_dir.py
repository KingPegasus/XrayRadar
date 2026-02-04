"""Tests for _get_web_dist_dir function in web.py."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from xrayradar_server.routers.web import _get_web_dist_dir


def test_get_web_dist_dir_from_env(monkeypatch, tmp_path):
    """Test _get_web_dist_dir when XRAYRADAR_WEB_DIST is set."""
    custom_path = tmp_path / "custom-web"
    custom_path.mkdir()
    monkeypatch.setenv("XRAYRADAR_WEB_DIST", str(custom_path))
    
    result = _get_web_dist_dir()
    assert result == custom_path


def test_get_web_dist_dir_from_env_with_whitespace(monkeypatch, tmp_path):
    """Test _get_web_dist_dir when XRAYRADAR_WEB_DIST has whitespace."""
    custom_path = tmp_path / "custom-web"
    custom_path.mkdir()
    monkeypatch.setenv("XRAYRADAR_WEB_DIST", f"  {custom_path}  ")
    
    result = _get_web_dist_dir()
    assert result == custom_path


def test_get_web_dist_dir_default(monkeypatch):
    """Test _get_web_dist_dir when XRAYRADAR_WEB_DIST is not set."""
    monkeypatch.delenv("XRAYRADAR_WEB_DIST", raising=False)
    
    result = _get_web_dist_dir()
    # Should return default path relative to web.py location
    assert isinstance(result, Path)
    # Verify it's the expected default path structure
    assert "xrayradar-web" in str(result) or "dist" in str(result)


def test_get_web_dist_dir_empty_env(monkeypatch, tmp_path):
    """Test _get_web_dist_dir when XRAYRADAR_WEB_DIST is empty string."""
    monkeypatch.setenv("XRAYRADAR_WEB_DIST", "")
    
    result = _get_web_dist_dir()
    # Should fall back to default
    assert isinstance(result, Path)
