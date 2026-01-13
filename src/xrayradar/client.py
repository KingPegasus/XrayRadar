"""
Main client for the error tracking SDK
"""

import atexit
from datetime import datetime, timezone
import logging
import os
import sys
import threading
from typing import Any, Callable, Dict, List, Optional
import weakref

from .models import Breadcrumb, Context, Event, Level, Request, User
from .transport import DebugTransport, HttpTransport, NullTransport, Transport


def _close_weak_client(client_ref: "weakref.ReferenceType[ErrorTracker]") -> None:
    client = client_ref()
    if client is not None:
        client.close()


class ErrorTracker:
    """Main error tracking client"""

    _instance_ref: Optional["weakref.ReferenceType[ErrorTracker]"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation"""
        inst = cls._instance_ref() if cls._instance_ref else None
        if inst is None:
            with cls._lock:
                inst = cls._instance_ref() if cls._instance_ref else None
                if inst is None:
                    inst = super().__new__(cls)
                    cls._instance_ref = weakref.ref(inst)
        return inst

    def __init__(
        self,
        dsn: Optional[str] = None,
        debug: bool = False,
        environment: Optional[str] = None,
        release: Optional[str] = None,
        server_name: Optional[str] = None,
        sample_rate: float = 1.0,
        max_breadcrumbs: int = 100,
        before_send: Optional[Callable[[Event], Optional[Event]]] = None,
        transport: Optional[Transport] = None,
        auto_enabling_integrations: bool = True,
        send_default_pii: bool = False,
        **kwargs,
    ):
        """
        Initialize the error tracker client

        Args:
            dsn: Data Source Name for connecting to the server
            debug: Enable debug mode (prints to console instead of sending)
            environment: Environment name (e.g., "production", "development")
            release: Release version
            server_name: Server name
            sample_rate: Sampling rate (0.0 to 1.0)
            max_breadcrumbs: Maximum number of breadcrumbs to keep
            before_send: Callback to modify events before sending
            transport: Custom transport implementation
            auto_enabling_integrations: Whether to auto-enable framework integrations
        """
        # Reconfigure singleton on every init call (tests expect independent configs
        # across instantiations while still using the singleton instance).
        self._lock = threading.Lock()

        # Configuration
        self.dsn = dsn
        self.debug = debug
        self.environment = environment or os.getenv(
            "XRAYRADAR_ENVIRONMENT", "development")
        self.release = release or os.getenv("XRAYRADAR_RELEASE")
        self.server_name = server_name or os.getenv(
            "XRAYRADAR_SERVER_NAME", os.uname().nodename if hasattr(os, 'uname') else "unknown")
        self.sample_rate = max(0.0, min(1.0, sample_rate))
        self.max_breadcrumbs = max_breadcrumbs
        self.before_send = before_send
        self.auto_enabling_integrations = auto_enabling_integrations
        self.send_default_pii = send_default_pii or os.getenv(
            "XRAYRADAR_SEND_DEFAULT_PII", ""
        ).lower() in ("true", "1", "yes")

        # State
        self._enabled = bool(dsn or debug or transport)
        self._breadcrumbs: List[Breadcrumb] = []
        self._context = Context()
        self._logger = logging.getLogger(__name__)

        # Initialize transport
        if transport:
            self._transport = transport
        elif debug:
            self._transport = DebugTransport()
        elif dsn:
            self._transport = HttpTransport(dsn, **kwargs)
        else:
            self._transport = NullTransport()

        # Set default context
        self._context.environment = self.environment
        self._context.release = self.release
        self._context.server_name = self.server_name

        # Setup global exception handler
        if self._enabled and self.auto_enabling_integrations and self.dsn:
            self._setup_global_exception_handler()

        # Register cleanup
        atexit.register(_close_weak_client, weakref.ref(self))

    def _setup_global_exception_handler(self):
        """Setup global exception handler for uncaught exceptions"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't capture KeyboardInterrupt
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            self.capture_exception(exc_value)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

        sys.excepthook = handle_exception

    def is_enabled(self) -> bool:
        """Check if the client is enabled"""
        return self._enabled

    def capture_exception(
        self,
        exception: Optional[Exception] = None,
        level: Level = Level.ERROR,
        message: Optional[str] = None,
        **extra_context,
    ) -> Optional[str]:
        """
        Capture an exception

        Args:
            exception: Exception to capture (if None, uses current exception)
            level: Error level
            message: Custom message
            **extra_context: Additional context data

        Returns:
            Event ID if captured, None otherwise
        """
        if not self._enabled:
            return None

        # Sample events
        if not self._should_sample():
            return None

        # Get current exception if none provided
        if exception is None:
            exc_info = sys.exc_info()
            if exc_info[0] is None:
                raise ValueError(
                    "No exception provided and no current exception")
            exception = exc_info[1]

        # Create event
        event = Event.from_exception(exception, level, message, self._context)

        # Add extra context
        if extra_context:
            event.contexts.extra.update(extra_context)

        # Add breadcrumbs
        event.breadcrumbs = self._breadcrumbs.copy()

        # Apply fingerprint if needed
        if not event.fingerprint:
            event.fingerprint = self._generate_fingerprint(event)

        # Apply before_send callback
        if self.before_send:
            try:
                event = self.before_send(event)
                if event is None:
                    return None
            except Exception as e:
                self._logger.error(f"Error in before_send callback: {e}")
                return None

        # Send event
        try:
            event_data = self._sanitize_event_data(event.to_dict())
            self._transport.send_event(event_data)
            return event.event_id
        except Exception as e:
            self._logger.error(f"Failed to send event: {e}")
            return None

    def capture_message(
        self,
        message: str,
        level: Level = Level.ERROR,
        **extra_context,
    ) -> Optional[str]:
        """
        Capture a message

        Args:
            message: Message to capture
            level: Error level
            **extra_context: Additional context data

        Returns:
            Event ID if captured, None otherwise
        """
        if not self._enabled:
            return None

        # Sample events
        if not self._should_sample():
            return None

        import uuid

        # Create event
        event = Event(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            contexts=self._context,
        )

        # Add extra context
        if extra_context:
            event.contexts.extra.update(extra_context)

        # Add breadcrumbs
        event.breadcrumbs = self._breadcrumbs.copy()

        # Apply fingerprint
        event.fingerprint = [message]

        # Apply before_send callback
        if self.before_send:
            try:
                event = self.before_send(event)
                if event is None:
                    return None
            except Exception as e:
                self._logger.error(f"Error in before_send callback: {e}")
                return None

        # Send event
        try:
            event_data = self._sanitize_event_data(event.to_dict())
            self._transport.send_event(event_data)
            return event.event_id
        except Exception as e:
            self._logger.error(f"Failed to send event: {e}")
            return None

    def add_breadcrumb(
        self,
        message: str,
        category: Optional[str] = None,
        level: Optional[Level] = None,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add a breadcrumb to the context

        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Breadcrumb level
            data: Additional data
            timestamp: Timestamp (defaults to now)
        """
        if not self._enabled:
            return

        breadcrumb = Breadcrumb(
            timestamp=timestamp or datetime.now(timezone.utc),
            message=message,
            category=category,
            level=level,
            data=data or {},
        )

        with self._lock:
            self._breadcrumbs.append(breadcrumb)
            # Keep only the most recent breadcrumbs
            if len(self._breadcrumbs) > self.max_breadcrumbs:
                self._breadcrumbs = self._breadcrumbs[-self.max_breadcrumbs:]

    def set_user(self, **user_data) -> None:
        """Set user context"""
        if not self._enabled:
            return

        self._context.user = User(**user_data)

    def set_tag(self, key: str, value: str) -> None:
        """Set a tag"""
        if not self._enabled:
            return

        self._context.tags[key] = value

    def set_extra(self, key: str, value: Any) -> None:
        """Set extra context data"""
        if not self._enabled:
            return

        self._context.extra[key] = value

    def set_context(self, context_type: str, context_data: Dict[str, Any]) -> None:
        """Set context data"""
        if not self._enabled:
            return

        if context_type == "user":
            self._context.user = User(**context_data)
        elif context_type == "request":
            self._context.request = Request(**context_data)
        else:
            self._context.extra[context_type] = context_data

    def clear_breadcrumbs(self) -> None:
        """Clear all breadcrumbs"""
        with self._lock:
            self._breadcrumbs.clear()

    def flush(self, timeout: Optional[float] = None) -> None:
        """Flush any pending events"""
        if self._transport:
            self._transport.flush(timeout)

    def close(self) -> None:
        """Close the client and cleanup resources"""
        self.flush()
        if hasattr(self._transport, "close"):
            self._transport.close()

    def _sanitize_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize event data based on privacy settings."""
        if self.send_default_pii:
            return event_data

        sanitized = dict(event_data)
        contexts = sanitized.get("contexts") or {}

        # Keep explicitly-set user context, but strip sensitive fields by default.
        user_ctx = contexts.get("user")
        if isinstance(user_ctx, dict):
            user_ctx = dict(user_ctx)
            user_ctx.pop("ip_address", None)
            contexts["user"] = user_ctx
        else:
            contexts["user"] = None

        # Sanitize request context.
        request_ctx = contexts.get("request")
        if isinstance(request_ctx, dict):
            url = request_ctx.get("url")
            if isinstance(url, str):
                request_ctx["url"] = url.split("?", 1)[0]

            headers = request_ctx.get("headers")
            if isinstance(headers, dict):
                request_ctx["headers"] = self._filter_headers(headers)

            request_ctx["query_string"] = None

            env = request_ctx.get("env")
            if isinstance(env, dict):
                env = dict(env)
                env.pop("REMOTE_ADDR", None)
                request_ctx["env"] = env

            # Some integrations pass remote_addr directly.
            request_ctx.pop("remote_addr", None)
            contexts["request"] = request_ctx

        # Many call-sites pass request/user through extra context (e.g. capture_exception(request=...)).
        extra = contexts.get("extra")
        if isinstance(extra, dict):
            extra = dict(extra)

            if isinstance(extra.get("user"), dict):
                extra.pop("user", None)

            extra_request = extra.get("request")
            if isinstance(extra_request, dict):
                extra_request = dict(extra_request)

                url = extra_request.get("url")
                if isinstance(url, str):
                    extra_request["url"] = url.split("?", 1)[0]

                headers = extra_request.get("headers")
                if isinstance(headers, dict):
                    extra_request["headers"] = self._filter_headers(headers)

                extra_request["query_string"] = None
                extra_request.pop("remote_addr", None)
                extra["request"] = extra_request

            contexts["extra"] = extra

        sanitized["contexts"] = contexts
        return sanitized

    def _filter_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        sensitive = {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-forwarded-authorization",
        }
        filtered: Dict[str, Any] = {}
        for k, v in headers.items():
            if isinstance(k, str) and k.lower() in sensitive:
                continue
            filtered[k] = v
        return filtered

    def _should_sample(self) -> bool:
        """Check if the event should be sampled"""
        import secrets
        return secrets.SystemRandom().random() < self.sample_rate

    def _generate_fingerprint(self, event: Event) -> List[str]:
        """Generate fingerprint for event"""
        if event.exception:
            # Use exception type and module for fingerprint
            fingerprint = [event.exception.type]
            if event.exception.module:
                fingerprint.append(event.exception.module)

            # Add top frame function if available
            if event.exception.stacktrace:
                top_frame = event.exception.stacktrace[0]
                fingerprint.append(top_frame.function)

            return fingerprint
        else:
            # Use message for non-exception events
            return [event.message]


# Global instance.
_client: Optional[ErrorTracker] = None


def init(**kwargs) -> ErrorTracker:
    """Initialize the global error tracker client"""
    global _client
    _client = ErrorTracker(**kwargs)
    return _client


def get_client() -> Optional[ErrorTracker]:
    """Get the global error tracker client"""
    return _client


def reset_global() -> None:
    """Reset the global client."""
    global _client
    if _client is not None:
        _client.close()
    _client = None


def capture_exception(*args, **kwargs) -> Optional[str]:
    """Capture an exception using the global client"""
    # If caller didn't pass an exception and there is no active exception,
    # do not raise (tests expect a no-op returning None).
    if not args and not kwargs and sys.exc_info()[0] is None:
        return None
    client = get_client()
    if client:
        try:
            result = client.capture_exception(*args, **kwargs)
        except ValueError:
            result = None
        return result
    return None


def capture_message(message: str, *args, **kwargs) -> Optional[str]:
    """Capture a message using the global client"""
    client = get_client()
    if client:
        result = client.capture_message(message, *args, **kwargs)
        return result
    return None


def add_breadcrumb(*args, **kwargs) -> None:
    """Add a breadcrumb using the global client"""
    client = get_client()
    if client:
        client.add_breadcrumb(*args, **kwargs)


def set_user(**user_data) -> None:
    """Set user context using the global client"""
    client = get_client()
    if client:
        client.set_user(**user_data)


def set_tag(key: str, value: str) -> None:
    """Set a tag using the global client"""
    client = get_client()
    if client:
        client.set_tag(key, value)


def set_extra(key: str, value: Any) -> None:
    """Set extra context data using the global client"""
    client = get_client()
    if client:
        client.set_extra(key, value)
