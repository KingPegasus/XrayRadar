"""
Graphene (GraphQL) integration for error tracking.

GraphQL frameworks often catch resolver exceptions and return them as part of the
GraphQL response, so Django's normal exception hooks may not see them.

This middleware captures resolver exceptions and forwards them to xrayradar.
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import ErrorTracker, get_client


class GrapheneIntegration:
    """Graphene middleware that captures resolver exceptions."""

    def __init__(self, client: Optional[ErrorTracker] = None):
        self.client = client

    def resolve(self, next_, root, info, **kwargs):
        try:
            return next_(root, info, **kwargs)
        except Exception as exc:
            client = self.client or get_client()
            if client is None:
                client = ErrorTracker()

            request = getattr(info, "context", None)
            request_data: Optional[dict[str, Any]] = None
            if request is not None and hasattr(request, "build_absolute_uri"):
                headers = dict(getattr(request, "headers", {}) or {})
                request_data = {
                    "url": request.build_absolute_uri(),
                    "method": getattr(request, "method", None),
                    "headers": headers,
                    "query_string": request.META.get("QUERY_STRING", "") if hasattr(request, "META") else "",
                    "remote_addr": request.META.get("REMOTE_ADDR") if hasattr(request, "META") else None,
                }

            operation_type = None
            try:
                operation = getattr(info, "operation", None)
                if operation is not None and getattr(operation, "operation", None) is not None:
                    operation_type = str(operation.operation)
            except Exception:
                operation_type = None

            tags: dict[str, str] = {"framework": "graphene"}
            if operation_type:
                tags["operation"] = operation_type

            client.capture_exception(
                exc, request=request_data or {}, tags=tags)
            raise
