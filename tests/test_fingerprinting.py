"""Tests for fingerprinting module"""

import pytest

from xrayradar_server.fingerprinting import compute_fingerprint


def test_fingerprint_with_sdk_fingerprint_list():
    """Test fingerprinting with SDK-provided fingerprint list"""
    event = {
        "fingerprint": ["key1", "key2", "key3"],
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash (64 hex characters)


def test_fingerprint_with_empty_list():
    """Test fingerprinting with empty fingerprint list falls back to exception/message"""
    event = {
        "fingerprint": [],
        "message": "Test error message",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_none_values_in_list():
    """Test fingerprinting filters out None values"""
    event = {
        "fingerprint": ["key1", None, "key2", None],
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception():
    """Test fingerprinting with exception data"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "Invalid value",
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_and_stacktrace():
    """Test fingerprinting with exception and stacktrace"""
    event = {
        "exception": {
            "values": [{
                "type": "KeyError",
                "value": "missing_key",
                "stacktrace": {
                    "frames": [
                        {
                            "filename": "test.py",
                            "function": "test_func",
                            "lineno": 42,
                            "in_app": True,
                        }
                    ]
                }
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_in_app_frame():
    """Test fingerprinting prefers in_app frames"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "Error",
                "stacktrace": {
                    "frames": [
                        {
                            "filename": "site-packages/lib.py",
                            "function": "lib_func",
                            "lineno": 10,
                            "in_app": False,
                        },
                        {
                            "filename": "app.py",
                            "function": "app_func",
                            "lineno": 20,
                            "in_app": True,
                        }
                    ]
                }
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_no_in_app_frame():
    """Test fingerprinting uses first frame if no in_app frame"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "Error",
                "stacktrace": {
                    "frames": [
                        {
                            "filename": "lib.py",
                            "function": "lib_func",
                            "lineno": 10,
                            "in_app": False,
                        }
                    ]
                }
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_empty_frames():
    """Test fingerprinting with empty frames list"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "Error",
                "stacktrace": {
                    "frames": []
                }
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_non_dict_frame():
    """Test fingerprinting handles non-dict frames"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "Error",
                "stacktrace": {
                    "frames": ["not-a-dict", {"filename": "test.py", "function": "test", "lineno": 1}]
                }
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_non_dict_values():
    """Test fingerprinting handles non-dict exception values"""
    event = {
        "exception": {
            "values": ["not-a-dict"]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_non_list_values():
    """Test fingerprinting handles non-list exception values"""
    event = {
        "exception": {
            "values": "not-a-list"
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_non_dict_stacktrace():
    """Test fingerprinting handles non-dict stacktrace"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "Error",
                "stacktrace": "not-a-dict"
            }]
        },
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_non_dict_exception():
    """Test fingerprinting handles non-dict exception"""
    event = {
        "exception": "not-a-dict",
        "message": "Test error",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_fallback_to_message():
    """Test fingerprinting falls back to message when no exception"""
    event = {
        "message": "Test error message",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_fallback_to_unknown():
    """Test fingerprinting falls back to 'unknown' when no message or exception"""
    event = {}
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash
    # Should hash "unknown"
    assert result == compute_fingerprint({"message": "unknown"})


def test_fingerprint_with_empty_message():
    """Test fingerprinting with empty message"""
    event = {
        "message": "",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash


def test_fingerprint_with_exception_no_value():
    """Test fingerprinting with exception but no value uses message"""
    event = {
        "exception": {
            "values": [{
                "type": "ValueError",
                "value": "",
            }]
        },
        "message": "Test error message",
    }
    result = compute_fingerprint(event)
    assert isinstance(result, str)
    assert len(result) == 64  # Full SHA256 hash
