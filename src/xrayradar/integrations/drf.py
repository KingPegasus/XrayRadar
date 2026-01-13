"""Django REST Framework integration for error tracking.

DRF typically handles exceptions and converts them into HTTP responses via its
exception handler. As a result, the exception may not propagate to Django's
normal exception hooks.

This module provides a wrapper for DRF's exception handler.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..client import ErrorTracker, get_client


try:
    from rest_framework.views import exception_handler as drf_exception_handler
except Exception:  # pragma: no cover
    drf_exception_handler = None


DRFExceptionHandler = Callable[[Exception, Dict[str, Any]], Any]


def make_drf_exception_handler(
    handler: Optional[DRFExceptionHandler] = None,
    client: Optional[ErrorTracker] = None,
) -> DRFExceptionHandler:
    """Create a DRF exception handler that reports to xrayradar.

    Usage in Django settings:

        REST_FRAMEWORK = {
            "EXCEPTION_HANDLER": "path.to.make_drf_exception_handler()"  # or set directly
        }

    Prefer importing this function and setting the handler directly.
    """

    def _handler(exc: Exception, context: Dict[str, Any]):
        effective_handler = handler
        if effective_handler is None:
            if drf_exception_handler is None:
                raise ImportError("djangorestframework is not installed")
            effective_handler = drf_exception_handler

        response = effective_handler(exc, context)

        effective_client = client or get_client() or ErrorTracker()

        request = context.get("request") if isinstance(context, dict) else None
        request_data: Dict[str, Any] = {}
        if request is not None and hasattr(request, "build_absolute_uri"):
            headers = dict(getattr(request, "headers", {}) or {})
            request_data = {
                "url": request.build_absolute_uri(),
                "method": getattr(request, "method", None),
                "headers": headers,
                "query_string": request.META.get("QUERY_STRING", "") if hasattr(request, "META") else "",
                "remote_addr": request.META.get("REMOTE_ADDR") if hasattr(request, "META") else None,
            }

        status_code = getattr(response, "status_code", None)
        tags: Dict[str, str] = {"framework": "drf"}
        if status_code is not None:
            tags["http_status"] = str(status_code)

        # Capture exceptions that map to server errors (5xx) or when DRF doesn't handle them.
        if response is None or (status_code is not None and int(status_code) >= 500):
            effective_client.capture_exception(
                exc, request=request_data, tags=tags)

        return response

    return _handler
