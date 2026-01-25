"""Tests for version module"""

import pytest
from importlib import metadata
from unittest.mock import patch, MagicMock

from xrayradar.version import get_version, get_sdk_info


class TestGetVersion:
    """Tests for get_version function"""

    def test_get_version_success(self):
        """Test get_version when metadata.version succeeds"""
        with patch("xrayradar.version.metadata.version", return_value="0.2.0"):
            version = get_version()
            assert version == "0.2.0"

    def test_get_version_fallback(self):
        """Test get_version when metadata.version fails (exception case)"""
        with patch("xrayradar.version.metadata.version", side_effect=Exception("Package not found")):
            version = get_version()
            assert version == "0.0.0"

    def test_get_version_metadata_not_found(self):
        """Test get_version when metadata.version raises PackageNotFoundError"""
        try:
            # PackageNotFoundError is available in Python 3.8+
            NotFoundError = metadata.PackageNotFoundError
        except AttributeError:
            # Fallback for older Python versions
            NotFoundError = Exception
        with patch("xrayradar.version.metadata.version", side_effect=NotFoundError("xrayradar")):
            version = get_version()
            assert version == "0.0.0"


class TestGetSdkInfo:
    """Tests for get_sdk_info function"""

    def test_get_sdk_info(self):
        """Test get_sdk_info returns correct structure"""
        with patch("xrayradar.version.get_version", return_value="0.2.0"):
            info = get_sdk_info()
            assert isinstance(info, dict)
            assert info["name"] == "xrayradar"
            assert info["version"] == "0.2.0"

    def test_get_sdk_info_calls_get_version(self):
        """Test that get_sdk_info calls get_version"""
        with patch("xrayradar.version.get_version", return_value="1.0.0") as mock_get_version:
            info = get_sdk_info()
            mock_get_version.assert_called_once()
            assert info["version"] == "1.0.0"
