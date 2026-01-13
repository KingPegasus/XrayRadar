"""
Custom exceptions for xrayradar
"""


class ErrorTrackerException(Exception):
    """Base exception for all error tracker SDK errors"""
    pass


class ConfigurationError(ErrorTrackerException):
    """Raised when there's a configuration error"""
    pass


class TransportError(ErrorTrackerException):
    """Raised when there's an error sending data to the server"""
    pass


class RateLimitedError(TransportError):
    """Raised when the client is rate limited"""
    pass


class InvalidDsnError(ConfigurationError):
    """Raised when the DSN is invalid"""
    pass
