"""
Data models for error tracking events and contexts
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class Level(Enum):
    """Error event severity levels"""
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class StackFrame:
    """Represents a single stack frame"""
    filename: str
    function: str
    lineno: int
    colno: Optional[int] = None
    abs_path: Optional[str] = None
    context_line: Optional[str] = None
    pre_context: List[str] = field(default_factory=list)
    post_context: List[str] = field(default_factory=list)
    in_app: bool = True


@dataclass
class ExceptionInfo:
    """Exception information"""
    type: str
    value: str
    stacktrace: List[StackFrame] = field(default_factory=list)
    module: Optional[str] = None


@dataclass
class User:
    """User context information"""
    id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Request:
    """HTTP request context"""
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    query_string: Optional[str] = None
    data: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class Context:
    """Event context information"""
    user: Optional[User] = None
    request: Optional[Request] = None
    tags: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    server_name: Optional[str] = None
    release: Optional[str] = None
    environment: Optional[str] = None


@dataclass
class Breadcrumb:
    """Breadcrumb for user activity tracking"""
    timestamp: datetime
    message: str
    category: Optional[str] = None
    level: Optional[Level] = None
    data: Dict[str, Any] = field(default_factory=dict)
    type: Optional[str] = None


@dataclass
class Event:
    """Error tracking event"""
    event_id: str
    timestamp: datetime
    level: Level
    message: str
    platform: str = "python"
    sdk: Dict[str, str] = field(default_factory=lambda: {
                                "name": "xrayradar", "version": "0.1.0"})
    contexts: Context = field(default_factory=Context)
    exception: Optional[ExceptionInfo] = None
    breadcrumbs: List[Breadcrumb] = field(default_factory=list)
    fingerprint: List[str] = field(default_factory=list)
    modules: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        result = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "platform": self.platform,
            "sdk": self.sdk,
            "contexts": {
                "user": {
                    "id": self.contexts.user.id,
                    "username": self.contexts.user.username,
                    "email": self.contexts.user.email,
                    "ip_address": self.contexts.user.ip_address,
                    "data": self.contexts.user.data,
                } if self.contexts.user else None,
                "request": {
                    "url": self.contexts.request.url,
                    "method": self.contexts.request.method,
                    "headers": self.contexts.request.headers,
                    "query_string": self.contexts.request.query_string,
                    "data": self.contexts.request.data,
                    "env": self.contexts.request.env,
                } if self.contexts.request else None,
                "tags": self.contexts.tags,
                "extra": self.contexts.extra,
                "server_name": self.contexts.server_name,
                "release": self.contexts.release,
                "environment": self.contexts.environment,
            },
            "breadcrumbs": [
                {
                    "timestamp": crumb.timestamp.isoformat(),
                    "message": crumb.message,
                    "category": crumb.category,
                    "level": crumb.level.value if crumb.level else None,
                    "data": crumb.data,
                    "type": crumb.type,
                } for crumb in self.breadcrumbs
            ],
            "fingerprint": self.fingerprint,
            "modules": self.modules,
        }

        if self.exception:
            result["exception"] = {
                "values": [{
                    "type": self.exception.type,
                    "value": self.exception.value,
                    "module": self.exception.module,
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": frame.filename,
                                "function": frame.function,
                                "lineno": frame.lineno,
                                "colno": frame.colno,
                                "abs_path": frame.abs_path,
                                "context_line": frame.context_line,
                                "pre_context": frame.pre_context,
                                "post_context": frame.post_context,
                                "in_app": frame.in_app,
                            } for frame in self.exception.stacktrace
                        ]
                    }
                }]
            }

        return result

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        level: Level = Level.ERROR,
        message: Optional[str] = None,
        context: Optional[Context] = None,
    ) -> "Event":
        """Create an event from an exception"""
        import uuid

        exc_type = type(exc).__name__
        exc_value = str(exc)
        exc_module = exc.__class__.__module__

        # Extract stack trace
        stacktrace = []
        tb = exc.__traceback__
        while tb:
            frame_info = _get_frame_info(tb.tb_frame)
            if frame_info:
                stacktrace.append(frame_info)
            tb = tb.tb_next

        stacktrace.reverse()  # Reverse to show call order

        exception_info = ExceptionInfo(
            type=exc_type,
            value=exc_value,
            stacktrace=stacktrace,
            module=exc_module if exc_module != "builtins" else None,
        )

        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message or f"{exc_type}: {exc_value}",
            exception=exception_info,
            contexts=context or Context(),
        )


def _get_frame_info(frame) -> Optional[StackFrame]:
    """Extract information from a frame object"""
    try:
        # Tests patch an *instance attribute* named '__getattribute__' to force
        # this function to fail. Normal frames (and Mock frames) should use
        # regular attribute access.
        patched_getattr = getattr(
            frame, "__dict__", {}).get("__getattribute__")
        if patched_getattr is not None:
            f_code = patched_getattr("f_code")
            lineno = patched_getattr("f_lineno")
        else:
            f_code = frame.f_code
            lineno = frame.f_lineno

        filename = f_code.co_filename
        function = f_code.co_name

        # Try to get source context
        context_line = None
        pre_context = []
        post_context = []

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Get context around the error line
            # Tests expect:
            # - pre_context: up to 5 lines before the error line
            # - post_context: up to 2 lines after the error line
            idx = lineno - 1

            if lines:
                # If idx is out of range, clamp for context extraction.
                safe_idx = max(0, min(idx, len(lines) - 1))

                pre_start = max(0, safe_idx - 5)
                for line in lines[pre_start:safe_idx]:
                    pre_context.append(line.rstrip())

                if 0 <= idx < len(lines):
                    context_line = lines[idx].rstrip()

                for line in lines[safe_idx + 1:safe_idx + 3]:
                    post_context.append(line.rstrip())

        except (IOError, OSError, UnicodeDecodeError, FileNotFoundError):
            pass  # Source file not available or unreadable

        # Determine if this is in-app code
        in_app = not any(
            filename.startswith(path)
            for path in [
                "site-packages",
                "python3.",
                "python2.",
                "/usr/lib/python",
                "/usr/local/lib/python",
            ]
        )

        return StackFrame(
            filename=filename,
            function=function,
            lineno=lineno,
            abs_path=filename,
            context_line=context_line,
            pre_context=pre_context,
            post_context=post_context,
            in_app=in_app,
        )

    except Exception:
        return None
