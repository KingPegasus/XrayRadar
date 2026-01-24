from __future__ import annotations

from importlib import metadata


def get_version() -> str:
    """
    Return the installed package version.

    Falls back to a safe placeholder when package metadata is unavailable
    (e.g. running from source without installation).
    """
    try:
        return metadata.version("xrayradar")
    except Exception:
        return "0.0.0"


def get_sdk_info() -> dict[str, str]:
    return {"name": "xrayradar", "version": get_version()}

