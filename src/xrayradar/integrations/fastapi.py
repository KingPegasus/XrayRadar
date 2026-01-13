"""
FastAPI integration for error tracking
"""

from typing import Any, Dict, Optional

from ..client import ErrorTracker
from ..models import Request as RequestModel

try:
    from fastapi import FastAPI, Request
    from fastapi.exceptions import RequestValidationError
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.exceptions import HTTPException as StarletteHTTPException
except ImportError:
    FastAPI = None
    Request = None
    Response = None
    RequestValidationError = None
    BaseHTTPMiddleware = None
    StarletteHTTPException = None


class FastAPIIntegration:
    """FastAPI integration for automatic error tracking"""

    def __init__(self, fastapi_app: Optional[FastAPI] = None):
        """
        Initialize FastAPI integration

        Args:
            fastapi_app: FastAPI app instance (optional, can be set later)
        """
        self.fastapi_app = fastapi_app
        self.client: Optional[ErrorTracker] = None

        if fastapi_app:
            self.init_app(fastapi_app)

    def init_app(self, fastapi_app: FastAPI, client: Optional[ErrorTracker] = None) -> None:
        """
        Initialize integration with FastAPI app

        Args:
            fastapi_app: FastAPI app instance
            client: ErrorTracker client instance
        """
        if FastAPI is None:
            raise ImportError("FastAPI is not installed")

        self.fastapi_app = fastapi_app
        self.client = client or ErrorTracker()

        # Add exception handlers
        fastapi_app.add_exception_handler(Exception, self._handle_exception)
        fastapi_app.add_exception_handler(
            RequestValidationError, self._handle_validation_error)
        fastapi_app.add_exception_handler(
            StarletteHTTPException, self._handle_http_exception)

        # Add middleware for request context
        fastapi_app.add_middleware(ErrorTrackerMiddleware, client=self.client)

    async def _handle_exception(self, request: Request, exc: Exception):
        """Handle general exceptions"""
        if not self.client:
            raise exc  # Re-raise if no client

        # Extract request information
        request_data = await self._extract_request_data(request)

        # Capture exception
        self.client.capture_exception(
            exc,
            request=request_data,
            tags={"framework": "fastapi"},
        )

        # Re-raise the exception
        raise exc

    async def _handle_validation_error(self, request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        if not self.client:
            raise exc

        # Extract request information
        request_data = await self._extract_request_data(request)

        # Capture validation error
        self.client.capture_exception(
            exc,
            request=request_data,
            tags={"framework": "fastapi", "error_type": "validation"},
        )

        # Re-raise the exception
        raise exc

    async def _handle_http_exception(self, request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        if not self.client:
            raise exc

        # Extract request information
        request_data = await self._extract_request_data(request)

        # Capture HTTP exception
        self.client.capture_message(
            f"HTTP {exc.status_code}: {exc.detail}",
            level="warning" if exc.status_code < 500 else "error",
            request=request_data,
            tags={"framework": "fastapi", "http_status": str(exc.status_code)},
        )

        # Re-raise the exception
        raise exc

    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract request data for context"""
        headers = dict(request.headers)
        # Filter sensitive headers
        sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
        filtered_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive_headers
        }

        return {
            "url": str(request.url),
            "method": request.method,
            "headers": filtered_headers,
            "query_string": str(request.url.query) if request.url.query else None,
            "remote_addr": request.client.host if request.client else None,
        }


if BaseHTTPMiddleware is not None:
    class ErrorTrackerMiddleware(BaseHTTPMiddleware):
        """Middleware for FastAPI error tracking"""

        def __init__(self, app, client: Optional[ErrorTracker] = None):
            super().__init__(app)
            self.client = client or ErrorTracker()

        async def dispatch(self, request: Request, call_next):
            """Process request and track context"""
            if not self.client:
                return await call_next(request)

            # Clear breadcrumbs for new request
            self.client.clear_breadcrumbs()

            # Add request breadcrumb
            self.client.add_breadcrumb(
                message=f"{request.method} {request.url.path}",
                category="http",
                data={
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_string": str(request.url.query) if request.url.query else None,
                }
            )

            # Set request context
            headers = dict(request.headers)
            sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
            filtered_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in sensitive_headers
            }

            request_context = RequestModel(
                url=str(request.url),
                method=request.method,
                headers=filtered_headers,
                query_string=str(
                    request.url.query) if request.url.query else None,
                env={
                    'REMOTE_ADDR': request.client.host if request.client else 'unknown',
                    'SERVER_NAME': request.url.hostname,
                    'SERVER_PORT': str(request.url.port) if request.url.port else '80',
                }
            )

            self.client.set_context("request", {
                "url": request_context.url,
                "method": request_context.method,
                "headers": request_context.headers,
                "query_string": request_context.query_string,
                "env": request_context.env,
            })

            # Process request
            response = await call_next(request)

            return response
else:
    ErrorTrackerMiddleware = None


# Convenience function for easy setup
def init_fastapi_integration(fastapi_app: FastAPI, client: Optional[ErrorTracker] = None) -> FastAPIIntegration:
    """
    Initialize FastAPI integration

    Args:
        fastapi_app: FastAPI app instance
        client: ErrorTracker client instance

    Returns:
        FastAPIIntegration instance
    """
    integration = FastAPIIntegration(fastapi_app, client)
    return integration
