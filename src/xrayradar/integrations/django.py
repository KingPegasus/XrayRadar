"""
Django integration for error tracking
"""

from typing import Optional

from ..client import ErrorTracker, get_client
from ..models import Request as RequestModel

try:
    from django.core.signals import got_request_exception, request_started
except ImportError:
    got_request_exception = None
    request_started = None


class DjangoIntegration:
    """Django integration for automatic error tracking"""

    def __init__(self, client: Optional[ErrorTracker] = None):
        """
        Initialize Django integration

        Args:
            client: ErrorTracker client instance
        """
        self.client = client or ErrorTracker()

        if got_request_exception and request_started:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup Django signal handlers"""
        got_request_exception.connect(self._handle_exception)
        request_started.connect(self._handle_request_started)

    def _handle_request_started(self, sender, **kwargs):
        """Handle request started signal"""
        if not self.client:
            return

        # Clear breadcrumbs for new request
        self.client.clear_breadcrumbs()

        # Try to get request from kwargs
        request = kwargs.get('request')
        if not request:
            return

        # Add request breadcrumb
        self.client.add_breadcrumb(
            message=f"{request.method} {request.path}",
            category="http",
            data={
                "method": request.method,
                "url": request.build_absolute_uri(),
                "path": request.path,
                "query_string": request.META.get('QUERY_STRING', ''),
            }
        )

        # Set request context
        headers = dict(request.headers) if hasattr(request, 'headers') else {}
        # Filter sensitive headers
        sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
        filtered_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive_headers
        }

        request_context = RequestModel(
            url=request.build_absolute_uri(),
            method=request.method,
            headers=filtered_headers,
            query_string=request.META.get('QUERY_STRING', ''),
            env={
                'REMOTE_ADDR': self._get_client_ip(request),
                'SERVER_NAME': request.get_host(),
                'SERVER_PORT': request.META.get('SERVER_PORT', '80'),
            }
        )

        self.client.set_context("request", {
            "url": request_context.url,
            "method": request_context.method,
            "headers": request_context.headers,
            "query_string": request_context.query_string,
            "env": request_context.env,
        })

        # Set user context if authenticated
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            user_data = {
                "id": str(getattr(request.user, 'id', None)),
                "username": getattr(request.user, 'username', None),
                "email": getattr(request.user, 'email', None),
            }
            self.client.set_user(
                **{k: v for k, v in user_data.items() if v is not None})

    def _handle_exception(self, sender, **kwargs):
        """Handle exception signal"""
        if not self.client:
            return

        # Get exception from kwargs
        exception = kwargs.get('exception')
        if not exception:
            return

        # Get request from kwargs
        request = kwargs.get('request')

        # Extract request information
        request_data = {}
        if request:
            headers = dict(request.headers) if hasattr(
                request, 'headers') else {}
            sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
            filtered_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in sensitive_headers
            }
            request_data = {
                "url": request.build_absolute_uri(),
                "method": request.method,
                "headers": filtered_headers,
                "query_string": request.META.get('QUERY_STRING', ''),
                "remote_addr": self._get_client_ip(request),
            }

        # Capture exception with request context
        self.client.capture_exception(
            exception,
            request=request_data,
            tags={"framework": "django"},
        )

    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'


# Middleware for Django
class ErrorTrackerMiddleware:
    """Django middleware for error tracking"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.client = get_client() or ErrorTracker()
        self.integration = DjangoIntegration(self.client)

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Process exception through error tracker"""
        if self.client:
            headers = dict(request.headers) if hasattr(
                request, 'headers') else {}
            sensitive_headers = {'authorization', 'cookie', 'set-cookie'}
            filtered_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in sensitive_headers
            }
            request_data = {
                "url": request.build_absolute_uri(),
                "method": request.method,
                "headers": filtered_headers,
                "query_string": request.META.get('QUERY_STRING', ''),
                "remote_addr": self.integration._get_client_ip(request),
            }

            self.client.capture_exception(
                exception,
                request=request_data,
                tags={"framework": "django"},
            )
            self.client.flush(timeout=1.0)
        return None


# Convenience function for easy setup
def init_django_integration(client: Optional[ErrorTracker] = None) -> DjangoIntegration:
    """
    Initialize Django integration

    Args:
        client: ErrorTracker client instance

    Returns:
        DjangoIntegration instance
    """
    integration = DjangoIntegration(client)
    return integration
