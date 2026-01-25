"""
Python logging integration for xrayradar

This integration captures log messages from Python's logging module and sends them
to XrayRadar as events. It can be configured to capture specific log levels and
exclude certain loggers.
"""

import logging
from typing import Optional, Set

from ..client import ErrorTracker, get_client
from ..models import Level


class LoggingIntegration:
    """Integration with Python's logging module"""

    def __init__(
        self,
        client: Optional[ErrorTracker] = None,
        level: int = logging.WARNING,
        logger: Optional[str] = None,
        exclude_loggers: Optional[Set[str]] = None,
    ):
        """
        Initialize logging integration

        Args:
            client: ErrorTracker client instance (optional, uses global client if not provided)
            level: Minimum log level to capture (default: logging.WARNING)
            logger: Specific logger name prefix to capture (None = all loggers)
            exclude_loggers: Set of logger names to exclude from capture
        """
        self.client = client
        self.level = level
        self.logger = logger
        self.exclude_loggers = exclude_loggers or set()
        self._handler: Optional[LoggingHandler] = None

    def setup(self, client: Optional[ErrorTracker] = None) -> None:
        """
        Setup the logging integration

        Args:
            client: ErrorTracker client instance (optional)
        """
        if self._handler is not None:
            # Already setup, remove old handler first
            logging.root.removeHandler(self._handler)

        self.client = client or self.client or get_client() or ErrorTracker()
        self._handler = LoggingHandler(
            client=self.client,
            level=self.level,
            logger=self.logger,
            exclude_loggers=self.exclude_loggers,
        )
        logging.root.addHandler(self._handler)

    def teardown(self) -> None:
        """Remove the logging integration"""
        if self._handler is not None:
            logging.root.removeHandler(self._handler)
            self._handler = None


class LoggingHandler(logging.Handler):
    """Custom logging handler that sends log records to XrayRadar"""

    # Map Python logging levels to XrayRadar levels
    LEVEL_MAP = {
        logging.DEBUG: Level.DEBUG,
        logging.INFO: Level.INFO,
        logging.WARNING: Level.WARNING,
        logging.ERROR: Level.ERROR,
        logging.CRITICAL: Level.FATAL,
    }

    def __init__(
        self,
        client: ErrorTracker,
        level: int = logging.WARNING,
        logger: Optional[str] = None,
        exclude_loggers: Optional[Set[str]] = None,
    ):
        """
        Initialize logging handler

        Args:
            client: ErrorTracker client instance
            level: Minimum log level to capture
            logger: Specific logger name to capture (None = all loggers)
            exclude_loggers: Set of logger names to exclude
        """
        super().__init__(level=level)
        self.client = client
        self.logger = logger
        self.exclude_loggers = exclude_loggers or set()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to XrayRadar

        Args:
            record: Log record to emit
        """
        try:
            # Skip if logger is excluded
            if record.name in self.exclude_loggers:
                return

            # Skip if specific logger is set and doesn't match
            # Check if record.name starts with the specified logger name
            if self.logger is not None:
                if not record.name.startswith(self.logger):
                    return

            # Skip if client is not enabled
            if not self.client._enabled:
                return

            # Map Python logging level to XrayRadar level
            xrayradar_level = self.LEVEL_MAP.get(record.levelno, Level.ERROR)

            # Build message
            message = self.format(record)

            # Capture as message (not exception unless it's an exception log)
            if record.exc_info:
                # If there's exception info, capture as exception
                exc_type, exc_value, exc_traceback = record.exc_info
                if exc_value:
                    self.client.capture_exception(
                        exc_value,
                        level=xrayradar_level,
                        message=message,
                        logger=record.name,
                        module=record.module,
                        funcName=record.funcName,
                        lineno=record.lineno,
                    )
                else:
                    self.client.capture_message(
                        message,
                        level=xrayradar_level,
                        logger=record.name,
                        module=record.module,
                        funcName=record.funcName,
                        lineno=record.lineno,
                    )
            else:
                # Regular log message
                self.client.capture_message(
                    message,
                    level=xrayradar_level,
                    logger=record.name,
                    module=record.module,
                    funcName=record.funcName,
                    lineno=record.lineno,
                )

        except Exception:
            # Don't let logging errors break the application
            self.handleError(record)


def setup_logging(
    client: Optional[ErrorTracker] = None,
    level: int = logging.WARNING,
    logger: Optional[str] = None,
    exclude_loggers: Optional[Set[str]] = None,
) -> LoggingIntegration:
    """
    Setup logging integration

    Args:
        client: ErrorTracker client instance (optional)
        level: Minimum log level to capture (default: logging.WARNING)
        logger: Specific logger name prefix to capture (None = all loggers)
        exclude_loggers: Set of logger names to exclude from capture

    Returns:
        LoggingIntegration instance

    Example:
        >>> import logging
        >>> from xrayradar import ErrorTracker
        >>> from xrayradar.integrations.logging import setup_logging
        >>>
        >>> tracker = ErrorTracker(dsn="https://xrayradar.com/your_project_id")
        >>> integration = setup_logging(client=tracker, level=logging.ERROR)
        >>>
        >>> # Now all ERROR and CRITICAL log messages will be sent to XrayRadar
        >>> logging.error("Something went wrong!")
    """
    integration = LoggingIntegration(
        client=client,
        level=level,
        logger=logger,
        exclude_loggers=exclude_loggers,
    )
    integration.setup(client)
    return integration
