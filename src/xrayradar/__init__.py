"""
xrayradar - A Python error tracking library
"""

from .client import (
    ErrorTracker,
    init,
    get_client,
    reset_global,
    capture_exception,
    capture_message,
    add_breadcrumb,
    set_user,
    set_tag,
    set_extra,
)
from .exceptions import ErrorTrackerException
from .models import Event, Level, Context

__version__ = "0.1.0"
__all__ = [
    "ErrorTracker",
    "ErrorTrackerException",
    "Event",
    "Level",
    "Context",
    "init",
    "get_client",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "set_user",
    "set_tag",
    "set_extra",
    "reset_global",
]
