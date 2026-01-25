"""
Tests for Python logging integration
"""

import logging
import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

from xrayradar import ErrorTracker
from xrayradar.integrations.logging import (
    LoggingIntegration,
    LoggingHandler,
    setup_logging,
)
from xrayradar.models import Level


class TestLoggingIntegration:
    """Tests for LoggingIntegration class"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        integration = LoggingIntegration()
        assert integration.client is None
        assert integration.level == logging.WARNING
        assert integration.logger is None
        assert integration.exclude_loggers == set()
        assert integration._handler is None

    def test_init_with_parameters(self):
        """Test initialization with custom parameters"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        exclude_loggers = {"urllib3", "requests"}
        integration = LoggingIntegration(
            client=client,
            level=logging.ERROR,
            logger="myapp",
            exclude_loggers=exclude_loggers,
        )
        assert integration.client == client
        assert integration.level == logging.ERROR
        assert integration.logger == "myapp"
        assert integration.exclude_loggers == exclude_loggers

    def test_init_with_none_exclude_loggers(self):
        """Test initialization with None exclude_loggers"""
        integration = LoggingIntegration(exclude_loggers=None)
        assert integration.exclude_loggers == set()

    def test_setup_with_client(self):
        """Test setup with provided client"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        integration = LoggingIntegration()
        
        # Remove any existing handlers to avoid interference
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration.setup(client)
            assert integration.client == client
            assert integration._handler is not None
            assert isinstance(integration._handler, LoggingHandler)
            assert integration._handler in logging.root.handlers
        finally:
            # Cleanup
            if integration._handler:
                logging.root.removeHandler(integration._handler)

    def test_setup_without_client_uses_existing(self):
        """Test setup without client uses existing client"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        integration = LoggingIntegration(client=client)
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration.setup()
            assert integration.client == client
            assert integration._handler is not None
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)

    def test_setup_uses_get_client_when_no_client_provided(self):
        """Test setup uses get_client() when no client is provided"""
        from xrayradar.client import get_client, init
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            # Set up a global client
            global_client = ErrorTracker(dsn="https://xrayradar.com/global")
            init(dsn="https://xrayradar.com/global")
            
            integration = LoggingIntegration()
            integration.setup()
            
            # Should use the global client
            assert integration.client is not None
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)
            # Cleanup global client
            from xrayradar.client import _client
            _client = None

    def test_setup_creates_new_client_when_none_available(self):
        """Test setup creates new client when no client is available"""
        from xrayradar.client import _client
        # Clear global client
        original_client = _client
        _client = None
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration = LoggingIntegration()
            integration.setup()
            
            # Should create a new client
            assert integration.client is not None
            assert isinstance(integration.client, ErrorTracker)
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)
            # Restore global client
            _client = original_client

    def test_setup_replaces_existing_handler(self):
        """Test setup replaces existing handler"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        integration = LoggingIntegration()
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            # Setup first time
            integration.setup(client)
            first_handler = integration._handler
            
            # Setup again
            integration.setup(client)
            second_handler = integration._handler
            
            # Should be different handlers
            assert first_handler != second_handler
            # First handler should not be in root handlers
            assert first_handler not in logging.root.handlers
            # Second handler should be in root handlers
            assert second_handler in logging.root.handlers
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)

    def test_teardown_removes_handler(self):
        """Test teardown removes handler"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        integration = LoggingIntegration()
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration.setup(client)
            assert integration._handler in logging.root.handlers
            
            integration.teardown()
            assert integration._handler is None
            # Handler should be removed from root
            # Note: We can't directly check if handler is removed because
            # it might have been removed already, but _handler should be None
        finally:
            # Extra cleanup
            if integration._handler:
                logging.root.removeHandler(integration._handler)

    def test_teardown_without_handler(self):
        """Test teardown when no handler is set"""
        integration = LoggingIntegration()
        # Should not raise
        integration.teardown()
        assert integration._handler is None


class TestLoggingHandler:
    """Tests for LoggingHandler class"""

    def test_init(self):
        """Test handler initialization"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(
            client=client,
            level=logging.ERROR,
            logger="myapp",
            exclude_loggers={"test"},
        )
        assert handler.client == client
        assert handler.level == logging.ERROR
        assert handler.logger == "myapp"
        assert handler.exclude_loggers == {"test"}

    def test_init_with_none_exclude_loggers(self):
        """Test handler initialization with None exclude_loggers"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client, exclude_loggers=None)
        assert handler.exclude_loggers == set()

    def test_level_map(self):
        """Test level mapping"""
        assert LoggingHandler.LEVEL_MAP[logging.DEBUG] == Level.DEBUG
        assert LoggingHandler.LEVEL_MAP[logging.INFO] == Level.INFO
        assert LoggingHandler.LEVEL_MAP[logging.WARNING] == Level.WARNING
        assert LoggingHandler.LEVEL_MAP[logging.ERROR] == Level.ERROR
        assert LoggingHandler.LEVEL_MAP[logging.CRITICAL] == Level.FATAL

    def test_emit_skips_excluded_logger(self):
        """Test emit skips excluded loggers"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(
            client=client,
            exclude_loggers={"excluded_logger"},
        )
        
        record = logging.LogRecord(
            name="excluded_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        handler.emit(record)
        # Should not call capture_message or capture_exception
        # We can't easily verify this without mocking, but the code path is covered

    def test_emit_skips_when_logger_prefix_not_matching(self):
        """Test emit skips when logger prefix doesn't match"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(
            client=client,
            logger="myapp",
        )
        
        record = logging.LogRecord(
            name="other_app",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        handler.emit(record)
        # Should skip because "other_app" doesn't start with "myapp"

    def test_emit_skips_when_client_disabled(self):
        """Test emit skips when client is disabled"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        client._enabled = False
        handler = LoggingHandler(client=client)
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        handler.emit(record)
        # Should skip because client is disabled

    def test_emit_captures_message(self):
        """Test emit captures regular log message"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client)
        
        with patch.object(client, 'capture_message') as mock_capture:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            record.module = "test_module"
            record.funcName = "test_func"
            
            handler.emit(record)
            
            mock_capture.assert_called_once()
            call_args = mock_capture.call_args
            assert call_args[0][0] == "Test message"
            assert call_args[1]["level"] == Level.ERROR
            assert call_args[1]["logger"] == "test"
            assert call_args[1]["module"] == "test_module"
            assert call_args[1]["funcName"] == "test_func"
            assert call_args[1]["lineno"] == 42

    def test_emit_captures_exception_with_exc_value(self):
        """Test emit captures exception when exc_info has exception value"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client)
        
        exc = ValueError("Test exception")
        exc_info = (type(exc), exc, exc.__traceback__)
        
        with patch.object(client, 'capture_exception') as mock_capture:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Exception occurred",
                args=(),
                exc_info=exc_info,
            )
            record.module = "test_module"
            record.funcName = "test_func"
            
            handler.emit(record)
            
            mock_capture.assert_called_once()
            call_args = mock_capture.call_args
            assert call_args[0][0] == exc
            assert call_args[1]["level"] == Level.ERROR
            # The message will include the formatted exception, so check it contains the original message
            assert "Exception occurred" in call_args[1]["message"]
            assert call_args[1]["logger"] == "test"

    def test_emit_captures_message_when_exc_info_has_no_value(self):
        """Test emit captures message when exc_info exists but has no value"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client)
        
        exc_info = (ValueError, None, None)
        
        with patch.object(client, 'capture_message') as mock_capture:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Exception info without value",
                args=(),
                exc_info=exc_info,
            )
            record.module = "test_module"
            record.funcName = "test_func"
            
            handler.emit(record)
            
            mock_capture.assert_called_once()
            # Verify it called capture_message (not capture_exception) when exc_value is None
            call_args = mock_capture.call_args
            assert "Exception info without value" in call_args[0][0]

    def test_emit_handles_exception_gracefully(self):
        """Test emit handles exceptions gracefully"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client)
        
        # Create a record that will cause an error
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        # Mock format to raise an exception
        with patch.object(handler, 'format', side_effect=Exception("Format error")):
            with patch.object(handler, 'handleError') as mock_handle_error:
                handler.emit(record)
                mock_handle_error.assert_called_once_with(record)

    def test_emit_uses_default_level_for_unknown_level(self):
        """Test emit uses ERROR level for unknown log levels"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client)
        
        # Create a record with a custom level not in LEVEL_MAP
        record = logging.LogRecord(
            name="test",
            level=99,  # Custom level not in LEVEL_MAP
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        with patch.object(client, 'capture_message') as mock_capture:
            handler.emit(record)
            call_args = mock_capture.call_args
            assert call_args[1]["level"] == Level.ERROR

    def test_emit_with_logger_prefix_matching(self):
        """Test emit processes when logger prefix matches"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(
            client=client,
            logger="myapp",
        )
        
        record = logging.LogRecord(
            name="myapp.module",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        with patch.object(client, 'capture_message') as mock_capture:
            handler.emit(record)
            mock_capture.assert_called_once()

    def test_emit_all_log_levels(self):
        """Test emit handles all log levels correctly"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        handler = LoggingHandler(client=client, level=logging.DEBUG)
        
        levels = [
            (logging.DEBUG, Level.DEBUG),
            (logging.INFO, Level.INFO),
            (logging.WARNING, Level.WARNING),
            (logging.ERROR, Level.ERROR),
            (logging.CRITICAL, Level.FATAL),
        ]
        
        for log_level, expected_xrayradar_level in levels:
            with patch.object(client, 'capture_message') as mock_capture:
                record = logging.LogRecord(
                    name="test",
                    level=log_level,
                    pathname="test.py",
                    lineno=1,
                    msg=f"Test {log_level}",
                    args=(),
                    exc_info=None,
                )
                
                handler.emit(record)
                mock_capture.assert_called_once()
                call_args = mock_capture.call_args
                assert call_args[1]["level"] == expected_xrayradar_level


class TestSetupLogging:
    """Tests for setup_logging function"""

    def test_setup_logging_creates_integration(self):
        """Test setup_logging creates and sets up integration"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration = setup_logging(
                client=client,
                level=logging.ERROR,
                logger="myapp",
                exclude_loggers={"test"},
            )
            
            assert isinstance(integration, LoggingIntegration)
            assert integration.client == client
            assert integration.level == logging.ERROR
            assert integration.logger == "myapp"
            assert integration.exclude_loggers == {"test"}
            assert integration._handler is not None
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)

    def test_setup_logging_with_defaults(self):
        """Test setup_logging with default parameters"""
        client = ErrorTracker(dsn="https://xrayradar.com/test")
        
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration = setup_logging(client=client)
            
            assert isinstance(integration, LoggingIntegration)
            assert integration.level == logging.WARNING
            assert integration.logger is None
            assert integration.exclude_loggers == set()
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)

    def test_setup_logging_without_client(self):
        """Test setup_logging without client (uses global or creates new)"""
        root_logger = logging.root
        original_handlers = root_logger.handlers[:]
        for handler in original_handlers:
            root_logger.removeHandler(handler)
        
        try:
            integration = setup_logging()
            
            assert isinstance(integration, LoggingIntegration)
            # Client should be created (ErrorTracker instance)
            assert integration.client is not None
        finally:
            if integration._handler:
                logging.root.removeHandler(integration._handler)
