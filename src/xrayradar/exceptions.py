"""
Custom exceptions for xrayradar

All exceptions inherit from ErrorTrackerException and provide clear,
actionable error messages to help users resolve issues quickly.
"""


class ErrorTrackerException(Exception):
    """
    Base exception for all error tracker SDK errors
    
    All xrayradar-specific exceptions inherit from this class,
    making it easy to catch all SDK-related errors.
    """
    pass


class ConfigurationError(ErrorTrackerException):
    """
    Raised when there's a configuration error
    
    This typically indicates an issue with how the SDK is configured,
    such as an invalid DSN format or missing required parameters.
    
    Example:
        >>> raise ConfigurationError("DSN is required but not provided")
    """
    pass


class TransportError(ErrorTrackerException):
    """
    Raised when there's an error sending data to the XrayRadar server
    
    This indicates a network or server-side issue preventing event delivery.
    The SDK will include details about the failure in the error message.
    
    Example:
        >>> raise TransportError("Failed to send event: HTTP 500: Internal Server Error")
    """
    pass


class RateLimitedError(TransportError):
    """
    Raised when the client is rate limited by the XrayRadar server
    
    The server has temporarily limited requests. The error message includes
    the retry-after time. You should wait before sending more events.
    
    Example:
        >>> raise RateLimitedError("Rate limited. Retry after 60 seconds")
    """
    pass


class InvalidDsnError(ConfigurationError):
    """
    Raised when the DSN (Data Source Name) is invalid or malformed
    
    The DSN format should be: https://xrayradar.com/your_project_id
    Make sure you've copied the correct DSN from your XrayRadar project settings.
    
    Example:
        >>> raise InvalidDsnError("Invalid DSN format: https://example.com")
    """
    pass
