"""
Tests for the Error Tracker client
"""

from unittest.mock import Mock

import pytest

from xrayradar import ErrorTracker, Level
from xrayradar.transport import DebugTransport, NullTransport


class TestErrorTracker:
    """Test cases for ErrorTracker client"""

    def test_singleton_pattern(self):
        """Test that ErrorTracker follows singleton pattern"""
        client1 = ErrorTracker(debug=True)
        client2 = ErrorTracker(debug=True)
        assert client1 is client2

    def test_initialization_with_debug_transport(self):
        """Test initialization with debug transport"""
        client = ErrorTracker(debug=True)
        assert isinstance(client._transport, DebugTransport)
        assert client.is_enabled()

    def test_initialization_without_dsn(self):
        """Test initialization without DSN creates null transport"""
        client = ErrorTracker()
        assert isinstance(client._transport, NullTransport)
        assert not client.is_enabled()

    def test_capture_exception(self):
        """Test capturing an exception"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = client.capture_exception(e)

            assert event_id is not None
            transport.send_event.assert_called_once()

            # Check the sent event data
            call_args = transport.send_event.call_args[0][0]
            assert call_args["level"] == "error"
            assert "Test error" in call_args["message"]
            assert "exception" in call_args

    def test_capture_exception_without_exception(self):
        """Test capturing current exception when none provided"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        try:
            raise ValueError("Test error")
        except Exception:
            event_id = client.capture_exception()

            assert event_id is not None
            transport.send_event.assert_called_once()

    def test_capture_exception_with_no_current_exception(self):
        """Test that capture_exception raises when no exception provided and no current exception"""
        client = ErrorTracker(debug=True)

        with pytest.raises(ValueError, match="No exception provided"):
            client.capture_exception()

    def test_capture_message(self):
        """Test capturing a message"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        event_id = client.capture_message("Test message", Level.WARNING)

        assert event_id is not None
        transport.send_event.assert_called_once()

        # Check the sent event data
        call_args = transport.send_event.call_args[0][0]
        assert call_args["level"] == "warning"
        assert call_args["message"] == "Test message"
        assert "exception" not in call_args

    def test_add_breadcrumb(self):
        """Test adding breadcrumbs"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        client.add_breadcrumb(
            "Test breadcrumb", category="test", level=Level.INFO)

        try:
            raise ValueError("Test error")
        except Exception as e:
            client.capture_exception(e)

            # Check that breadcrumb was included
            call_args = transport.send_event.call_args[0][0]
            assert len(call_args["breadcrumbs"]) == 1
            assert call_args["breadcrumbs"][0]["message"] == "Test breadcrumb"
            assert call_args["breadcrumbs"][0]["category"] == "test"

    def test_set_user(self):
        """Test setting user context"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        client.set_user(id="123", email="test@example.com",
                        username="testuser")

        try:
            raise ValueError("Test error")
        except Exception as e:
            client.capture_exception(e)

            # Check that user context was included
            call_args = transport.send_event.call_args[0][0]
            user_context = call_args["contexts"]["user"]
            assert user_context["id"] == "123"
            assert user_context["email"] == "test@example.com"
            assert user_context["username"] == "testuser"

    def test_set_tag(self):
        """Test setting tags"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        client.set_tag("feature", "checkout")
        client.set_tag("locale", "en-US")

        try:
            raise ValueError("Test error")
        except Exception as e:
            client.capture_exception(e)

            # Check that tags were included
            call_args = transport.send_event.call_args[0][0]
            tags = call_args["contexts"]["tags"]
            assert tags["feature"] == "checkout"
            assert tags["locale"] == "en-US"

    def test_set_extra(self):
        """Test setting extra context"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        client.set_extra("cart_value", 99.99)
        client.set_extra("payment_method", "credit_card")

        try:
            raise ValueError("Test error")
        except Exception as e:
            client.capture_exception(e)

            # Check that extra context was included
            call_args = transport.send_event.call_args[0][0]
            extra = call_args["contexts"]["extra"]
            assert extra["cart_value"] == 99.99
            assert extra["payment_method"] == "credit_card"

    def test_before_send_callback(self):
        """Test before_send callback"""
        transport = Mock()

        def before_send(event):
            if "filtered" in event.message:
                return None  # Filter out
            event.contexts.tags["processed"] = "true"
            return event

        client = ErrorTracker(transport=transport, before_send=before_send)

        # Test filtered event
        try:
            raise ValueError("This should be filtered")
        except Exception as e:
            event_id = client.capture_exception(e, message="filtered message")
            assert event_id is None
            transport.send_event.assert_not_called()

        # Test processed event
        try:
            raise ValueError("This should be processed")
        except Exception as e:
            event_id = client.capture_exception(e)
            assert event_id is not None
            transport.send_event.assert_called_once()

            # Check that event was processed
            call_args = transport.send_event.call_args[0][0]
            assert call_args["contexts"]["tags"]["processed"] == "true"

    def test_sample_rate(self):
        """Test sampling functionality"""
        transport = Mock()
        client = ErrorTracker(transport=transport,
                              sample_rate=0.0)  # 0% sampling

        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = client.capture_exception(e)
            assert event_id is None  # Should be sampled out
            transport.send_event.assert_not_called()

    def test_max_breadcrumbs(self):
        """Test maximum breadcrumbs limit"""
        transport = Mock()
        client = ErrorTracker(transport=transport, max_breadcrumbs=2)

        # Add more breadcrumbs than the limit
        client.add_breadcrumb("Breadcrumb 1")
        client.add_breadcrumb("Breadcrumb 2")
        client.add_breadcrumb("Breadcrumb 3")

        try:
            raise ValueError("Test error")
        except Exception as e:
            client.capture_exception(e)

            # Check that only the most recent breadcrumbs are kept
            call_args = transport.send_event.call_args[0][0]
            assert len(call_args["breadcrumbs"]) == 2
            assert call_args["breadcrumbs"][0]["message"] == "Breadcrumb 2"
            assert call_args["breadcrumbs"][1]["message"] == "Breadcrumb 3"

    def test_clear_breadcrumbs(self):
        """Test clearing breadcrumbs"""
        transport = Mock()
        client = ErrorTracker(transport=transport)

        client.add_breadcrumb("Test breadcrumb")
        client.clear_breadcrumbs()

        try:
            raise ValueError("Test error")
        except Exception as e:
            client.capture_exception(e)

            # Check that no breadcrumbs were included
            call_args = transport.send_event.call_args[0][0]
            assert len(call_args["breadcrumbs"]) == 0

    def test_disabled_client(self):
        """Test that disabled client doesn't send events"""
        client = ErrorTracker()  # No DSN, so disabled

        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = client.capture_exception(e)
            assert event_id is None

    def test_configuration_defaults(self):
        """Test default configuration values"""
        client = ErrorTracker(debug=True)

        assert client.environment == "development"
        assert client.sample_rate == 1.0
        assert client.max_breadcrumbs == 100
        assert client.auto_enabling_integrations is True


class TestGlobalFunctions:
    """Test cases for global functions"""

    def setup_method(self):
        from xrayradar import reset_global
        reset_global()

    def test_init_and_get_client(self):
        """Test global client initialization and retrieval"""
        from xrayradar import init, get_client

        client = init(debug=True)
        assert client is get_client()
        assert isinstance(client, ErrorTracker)

    def test_global_capture_exception(self):
        """Test global capture_exception function"""
        from xrayradar import init, capture_exception

        init(debug=True)

        try:
            raise ValueError("Test error")
        except Exception:
            event_id = capture_exception()
            assert event_id is not None

    def test_global_capture_message(self):
        """Test global capture_message function"""
        from xrayradar import init, capture_message

        init(debug=True)

        event_id = capture_message("Test message")
        assert event_id is not None

    def test_global_functions_when_no_client(self):
        """Test global functions when no client is initialized"""
        from xrayradar import capture_exception, capture_message, add_breadcrumb, set_user, set_tag, set_extra

        # These should not raise exceptions when no client is initialized
        assert capture_exception() is None
        assert capture_message("test") is None
        add_breadcrumb("test")
        set_user(id="123")
        set_tag("key", "value")
        set_extra("key", "value")
