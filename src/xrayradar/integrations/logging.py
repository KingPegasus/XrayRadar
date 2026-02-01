"""
Python logging integration for xrayradar

This integration can either:
- Send log messages to XrayRadar as events (default), or
- Capture log messages as breadcrumbs (capture_as_breadcrumbs=True) so they appear
  in the breadcrumb timeline when an error is later captured (console-style auto-capture).
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
        capture_as_breadcrumbs: bool = False,
    ):
        """
        Initialize logging integration

        Args:
            client: ErrorTracker client instance (optional, uses global client if not provided)
            level: Minimum log level to capture (default: logging.WARNING)
            logger: Specific logger name prefix to capture (None = all loggers)
            exclude_loggers: Set of logger names to exclude from capture
            capture_as_breadcrumbs: If True, add log records as breadcrumbs (type=console)
                instead of sending them as events. Use for console-style auto-capture.
        """
        self.client = client
        self.level = level
        self.logger = logger
        self.exclude_loggers = exclude_loggers or set()
        self.capture_as_breadcrumbs = capture_as_breadcrumbs
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
            capture_as_breadcrumbs=self.capture_as_breadcrumbs,
        )
        logging.root.addHandler(self._handler)

    def teardown(self) -> None:
        """Remove the logging integration"""
        if self._handler is not None:
            logging.root.removeHandler(self._handler)
            self._handler = None


class LoggingHandler(logging.Handler):
    """Custom logging handler that sends log records to XrayRadar or adds them as breadcrumbs"""

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
        capture_as_breadcrumbs: bool = False,
    ):
        """
        Initialize logging handler

        Args:
            client: ErrorTracker client instance
            level: Minimum log level to capture
            logger: Specific logger name to capture (None = all loggers)
            exclude_loggers: Set of logger names to exclude
            capture_as_breadcrumbs: If True, add records as breadcrumbs (type=console) instead of events
        """
        super().__init__(level=level)
        self.client = client
        self.logger = logger
        self.exclude_loggers = exclude_loggers or set()
        self.capture_as_breadcrumbs = capture_as_breadcrumbs

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to XrayRadar (as event or as breadcrumb)

        Args:
            record: Log record to emit
        """
        try:
            # Skip if logger is excluded
            if record.name in self.exclude_loggers:
                return

            # Skip if specific logger is set and doesn't match
            if self.logger is not None:
                if not record.name.startswith(self.logger):
                    return

            # Skip if client is not enabled
            if not self.client._enabled:
                return

            # Map Python logging level to XrayRadar level
            xrayradar_level = self.LEVEL_MAP.get(record.levelno, Level.ERROR)
            message = self.format(record)

            if self.capture_as_breadcrumbs:
                # Auto-capture as console breadcrumb (appears in timeline when error is captured)
                self.client.add_breadcrumb(
                    message=message,
                    category=record.name,
                    level=xrayradar_level,
                    type="console",
                    data={
                        "logger": record.name,
                        "module": record.module,
                        "funcName": getattr(record, "funcName", None),
                        "lineno": getattr(record, "lineno", None),
                    },
                )
                return

            # Capture as message (not exception unless it's an exception log)
            if record.exc_info:
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
                self.client.capture_message(
                    message,
                    level=xrayradar_level,
                    logger=record.name,
                    module=record.module,
                    funcName=record.funcName,
                    lineno=record.lineno,
                )

        except Exception:
            self.handleError(record)


def setup_logging(
    client: Optional[ErrorTracker] = None,
    level: int = logging.WARNING,
    logger: Optional[str] = None,
    exclude_loggers: Optional[Set[str]] = None,
    capture_as_breadcrumbs: bool = False,
) -> LoggingIntegration:
    """
    Setup logging integration

    Args:
        client: ErrorTracker client instance (optional)
        level: Minimum log level to capture (default: logging.WARNING)
        logger: Specific logger name prefix to capture (None = all loggers)
        exclude_loggers: Set of logger names to exclude from capture
        capture_as_breadcrumbs: If True, log records are added as breadcrumbs (type=console)
            instead of being sent as events. Use for console-style auto-capture in the timeline.

    Returns:
        LoggingIntegration instance

    Example (events):
        >>> integration = setup_logging(client=tracker, level=logging.ERROR)
        >>> logging.error("Something went wrong!")  # sent as event

    Example (console breadcrumbs):
        >>> integration = setup_logging(client=tracker, level=logging.INFO, capture_as_breadcrumbs=True)
        >>> logging.info("User opened settings")  # added as breadcrumb; appears in timeline on error
    """
    integration = LoggingIntegration(
        client=client,
        level=level,
        logger=logger,
        exclude_loggers=exclude_loggers,
        capture_as_breadcrumbs=capture_as_breadcrumbs,
    )
    integration.setup(client)
    return integration
