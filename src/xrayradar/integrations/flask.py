"""
Flask integration for error tracking
"""

from typing import Optional

from ..client import ErrorTracker
from ..models import Request as RequestModel

try:
    from flask import Flask, request
    from flask.signals import got_request_exception, request_started
except ImportError:
    Flask = None
    request = None
    got_request_exception = None
    request_started = None


class FlaskIntegration:
    """Flask integration for automatic error tracking"""

    def __init__(self, flask_app: Optional[Flask] = None, client: Optional[ErrorTracker] = None):
        """
        Initialize Flask integration

        Args:
            flask_app: Flask app instance (optional, can be set later)
            client: ErrorTracker client instance (optional)
        """
        self.flask_app = flask_app
        self.client: Optional[ErrorTracker] = None

        if flask_app:
            self.init_app(flask_app, client)

    def init_app(self, flask_app: Flask, client: Optional[ErrorTracker] = None) -> None:
        """
        Initialize integration with Flask app

        Args:
            flask_app: Flask app instance
            client: ErrorTracker client instance
        """
        if Flask is None:
            raise ImportError("Flask is not installed")

        self.flask_app = flask_app
        self.client = client or ErrorTracker()

        # Setup request handlers
        got_request_exception.connect(self._handle_exception, flask_app)
        request_started.connect(self._handle_request_started, flask_app)

        # Add teardown handler
        @flask_app.teardown_appcontext
        def teardown(exc):
            if exc:
                self._handle_exception(flask_app, exc)

    def _handle_request_started(self, sender, **extra):
        """Handle request started signal"""
        if not self.client or not request:
            return

        # Clear breadcrumbs for new request
        self.client.clear_breadcrumbs()

        # Add request breadcrumb
        self.client.add_breadcrumb(
            message=f"{request.method} {request.path}",
            category="http",
            data={
                "method": request.method,
                "url": request.url,
                "path": request.path,
                "query_string": request.query_string.decode('utf-8') if request.query_string else None,
            }
        )

        # Set request context
        headers = dict(request.headers)
        # Filter sensitive headers
        sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
        filtered_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive_headers
        }

        request_context = RequestModel(
            url=request.url,
            method=request.method,
            headers=filtered_headers,
            query_string=request.query_string.decode(
                'utf-8') if request.query_string else None,
            env={
                'REMOTE_ADDR': request.remote_addr,
                'SERVER_NAME': request.host,
                'SERVER_PORT': str(request.environ.get('SERVER_PORT', '80')),
            }
        )

        self.client.set_context("request", {
            "url": request_context.url,
            "method": request_context.method,
            "headers": request_context.headers,
            "query_string": request_context.query_string,
            "env": request_context.env,
        })

    def _handle_exception(self, sender, exception, **extra):
        """Handle exception signal"""
        if not self.client:
            return

        # Extract request information
        request_data = {}
        if request:
            headers = dict(request.headers)
            sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
            filtered_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in sensitive_headers
            }

            request_data = {
                "url": request.url,
                "method": request.method,
                "headers": filtered_headers,
                "query_string": request.query_string.decode('utf-8') if request.query_string else None,
                "remote_addr": request.remote_addr,
            }

        # Capture exception with request context
        self.client.capture_exception(
            exception,
            request=request_data,
            tags={"framework": "flask"},
        )


# Convenience function for easy setup
def init_flask_integration(flask_app: Flask, client: Optional[ErrorTracker] = None) -> FlaskIntegration:
    """
    Initialize Flask integration

    Args:
        flask_app: Flask app instance
        client: ErrorTracker client instance

    Returns:
        FlaskIntegration instance
    """
    integration = FlaskIntegration(flask_app, client)
    return integration
