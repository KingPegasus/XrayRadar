"""
Transport layer for sending events to the error tracking server
"""

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import requests

from .exceptions import TransportError, RateLimitedError, InvalidDsnError


class Transport(ABC):
    """Abstract base class for transport implementations"""

    @abstractmethod
    def send_event(self, event_data: Dict[str, Any]) -> None:
        """Send an event to the server"""
        pass  # pragma: no cover

    @abstractmethod
    def flush(self, timeout: Optional[float] = None) -> None:
        """Flush any pending events"""
        pass  # pragma: no cover


class HttpTransport(Transport):
    """HTTP transport for sending events to a server"""

    def _redact_dsn(self, dsn: str) -> str:
        """Redact secrets from DSN for safe error reporting."""
        try:
            parsed = urlparse(dsn)
            if not parsed.scheme or not parsed.netloc:
                return "<invalid dsn>"

            hostname = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""
            path = parsed.path or ""

            # Keep username/public key if present, but never include password.
            if parsed.username:
                return f"{parsed.scheme}://{parsed.username}@{hostname}{port}{path}"
            return f"{parsed.scheme}://{hostname}{port}{path}"
        except Exception:
            return "<invalid dsn>"

    def __init__(
        self,
        dsn: str,
        auth_token: Optional[str] = None,
        timeout: float = 10.0,
        verify_ssl: bool = True,
        max_payload_size: int = 100 * 1024,  # 100KB
    ):
        """
        Initialize HTTP transport

        Args:
            dsn: Data Source Name (e.g., "https://public_key@host/project_id")
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            max_payload_size: Maximum payload size in bytes
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_payload_size = max_payload_size

        # Parse DSN
        parsed = self._parse_dsn(dsn)
        self.project_id = parsed["project_id"]
        self.server_url = parsed["server_url"]

        # Create session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "xrayradar/0.1.0",
        })

        token = (auth_token or "").strip() or os.getenv("XRAYRADAR_AUTH_TOKEN")
        if token:
            self.session.headers["X-Xrayradar-Token"] = token

    def _parse_dsn(self, dsn: str) -> Dict[str, str]:
        """Parse DSN string into components"""
        try:
            # Supported formats:
            # - {PROTOCOL}://{HOST}:{PORT}/{PROJECT_ID}
            parsed = urlparse(dsn)

            if not parsed.scheme or not parsed.netloc:
                raise InvalidDsnError(
                    f"Invalid DSN format: {self._redact_dsn(dsn)}")

            # Extract project ID from path
            path_parts = parsed.path.strip("/").split("/")
            if not path_parts:
                raise InvalidDsnError(
                    f"Missing project ID in DSN: {self._redact_dsn(dsn)}")

            project_id = path_parts[-1]
            if not project_id:
                raise InvalidDsnError(
                    f"Missing project ID in DSN: {self._redact_dsn(dsn)}")

            # Build server URL
            server_url = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                server_url += f":{parsed.port}"

            return {
                "project_id": project_id,
                "server_url": server_url,
            }

        except Exception as e:
            if isinstance(e, InvalidDsnError):
                raise
            raise InvalidDsnError(
                f"Failed to parse DSN: {self._redact_dsn(dsn)}") from e

    def send_event(self, event_data: Dict[str, Any]) -> None:
        """Send an event to the server"""
        try:
            # Check payload size
            payload = json.dumps(event_data)
            if len(payload.encode('utf-8')) > self.max_payload_size:
                # Truncate large payloads
                event_data = self._truncate_payload(event_data)
                payload = json.dumps(event_data)

            url = f"{self.server_url}/api/{self.project_id}/store/"

            response = self.session.post(
                url,
                data=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            # Handle response
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitedError(
                    f"Rate limited. Retry after {retry_after} seconds")

            elif response.status_code >= 400:
                body = (response.text or "").strip()
                if body:
                    body = body[:200]
                    error_msg = f"HTTP {response.status_code}: {body}"
                else:
                    error_msg = f"HTTP {response.status_code}"
                raise TransportError(f"Failed to send event: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise TransportError(
                f"Network error while sending event: {e}") from e
        except (ValueError, TypeError) as e:
            raise TransportError(f"Failed to encode event data: {e}") from e

    def _truncate_payload(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate large payloads to fit within size limits"""
        # Create a copy to avoid modifying the original
        truncated = event_data.copy()

        # Truncate large fields
        if "message" in truncated and len(truncated["message"]) > 1000:
            truncated["message"] = truncated["message"][:1000] + \
                "... (truncated)"

        # Truncate exception stack traces
        if "exception" in truncated and "values" in truncated["exception"]:
            for exc_value in truncated["exception"]["values"]:
                if "stacktrace" in exc_value and "frames" in exc_value["stacktrace"]:
                    frames = exc_value["stacktrace"]["frames"]
                    # Keep only the first 50 frames
                    if len(frames) > 50:
                        exc_value["stacktrace"]["frames"] = frames[:50]

        # Truncate breadcrumbs
        if "breadcrumbs" in truncated and len(truncated["breadcrumbs"]) > 100:
            truncated["breadcrumbs"] = truncated["breadcrumbs"][:100]

        return truncated

    def flush(self, timeout: Optional[float] = None) -> None:
        """Flush any pending events (no-op for HTTP transport)"""
        # HTTP transport sends events immediately, so no flushing needed
        pass


class DebugTransport(Transport):
    """Debug transport that prints events to console"""

    def send_event(self, event_data: Dict[str, Any]) -> None:
        """Print event to console for debugging"""
        print(
            f"[ErrorTracker] Event: {json.dumps(event_data, indent=2, default=str)}")

    def flush(self, timeout: Optional[float] = None) -> None:
        """No-op for debug transport"""
        pass


class NullTransport(Transport):
    """Null transport that discards all events"""

    def send_event(self, event_data: Dict[str, Any]) -> None:
        """Discard event"""
        pass

    def flush(self, timeout: Optional[float] = None) -> None:
        """No-op for null transport"""
        pass
