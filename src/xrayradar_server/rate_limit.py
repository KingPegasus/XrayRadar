"""Rate limiting for public endpoints using slowapi."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For when behind a proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def get_rate_limit_key_auth(request: Request) -> str:
    """Key function for IP-based rate limiting on auth endpoints."""
    return get_client_ip(request)


def get_rate_limit_key_token(request: Request) -> str:
    """Key function for token-based rate limiting on event ingestion."""
    token = (request.headers.get("X-Xrayradar-Token") or "").strip()
    return token or "no-token"


limiter = Limiter(key_func=get_remote_address, headers_enabled=False)
