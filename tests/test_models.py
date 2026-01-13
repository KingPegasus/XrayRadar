"""
Tests for the error tracker models
"""

from datetime import datetime, timezone
from unittest.mock import Mock, mock_open, patch

from xrayradar.models import (
    Breadcrumb,
    Context,
    Event,
    ExceptionInfo,
    Level,
    Request,
    StackFrame,
    User,
    _get_frame_info,
)


class TestLevel:
    """Test cases for Level enum"""

    def test_level_values(self):
        """Test level enum values"""
        assert Level.FATAL.value == "fatal"
        assert Level.ERROR.value == "error"
        assert Level.WARNING.value == "warning"
        assert Level.INFO.value == "info"
        assert Level.DEBUG.value == "debug"


class TestEvent:
    """Test cases for Event model"""

    def test_event_creation(self):
        """Test creating an event"""
        event = Event(
            event_id="test-id",
            timestamp=datetime.now(timezone.utc),
            level=Level.ERROR,
            message="Test message"
        )

        assert event.event_id == "test-id"
        assert event.level == Level.ERROR
        assert event.message == "Test message"
        assert event.platform == "python"
        assert "name" in event.sdk
        assert "version" in event.sdk

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        user = User(id="123", email="test@example.com")
        request = Request(url="http://example.com", method="GET")
        context = Context(user=user, request=request, tags={"key": "value"})

        breadcrumb = Breadcrumb(
            timestamp=datetime.now(timezone.utc),
            message="Test breadcrumb",
            category="test"
        )

        exception_info = ExceptionInfo(
            type="ValueError",
            value="Test error",
            stacktrace=[
                StackFrame(
                    filename="test.py",
                    function="test_func",
                    lineno=10
                )
            ]
        )

        event = Event(
            event_id="test-id",
            timestamp=datetime.now(timezone.utc),
            level=Level.ERROR,
            message="Test message",
            contexts=context,
            breadcrumbs=[breadcrumb],
            exception=exception_info
        )

        event_dict = event.to_dict()

        assert event_dict["event_id"] == "test-id"
        assert event_dict["level"] == "error"
        assert event_dict["message"] == "Test message"
        assert event_dict["platform"] == "python"
        assert event_dict["contexts"]["user"]["id"] == "123"
        assert event_dict["contexts"]["request"]["url"] == "http://example.com"
        assert event_dict["contexts"]["tags"]["key"] == "value"
        assert len(event_dict["breadcrumbs"]) == 1
        assert event_dict["breadcrumbs"][0]["message"] == "Test breadcrumb"
        assert "exception" in event_dict
        assert event_dict["exception"]["values"][0]["type"] == "ValueError"

    def test_event_from_exception(self):
        """Test creating event from exception"""
        try:
            raise ValueError("Test error message")
        except Exception as e:
            event = Event.from_exception(e)

            assert event.level == Level.ERROR
            assert "ValueError: Test error message" in event.message
            assert event.exception is not None
            assert event.exception.type == "ValueError"
            assert event.exception.value == "Test error message"
            assert event.exception.module is None  # built-in exception

    def test_event_from_exception_with_custom_message(self):
        """Test creating event from exception with custom message"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            event = Event.from_exception(e, message="Custom error message")

            assert event.message == "Custom error message"

    def test_event_from_exception_with_context(self):
        """Test creating event from exception with context"""
        context = Context(tags={"custom": "tag"})

        try:
            raise ValueError("Test error")
        except Exception as e:
            event = Event.from_exception(e, context=context)

            assert event.contexts.tags["custom"] == "tag"


class TestContext:
    """Test cases for Context model"""

    def test_context_creation(self):
        """Test creating context"""
        user = User(id="123")
        request = Request(url="http://example.com")

        context = Context(
            user=user,
            request=request,
            tags={"key": "value"},
            extra={"data": "test"},
            server_name="test-server",
            release="1.0.0",
            environment="production"
        )

        assert context.user == user
        assert context.request == request
        assert context.tags["key"] == "value"
        assert context.extra["data"] == "test"
        assert context.server_name == "test-server"
        assert context.release == "1.0.0"
        assert context.environment == "production"

    def test_context_defaults(self):
        """Test context default values"""
        context = Context()

        assert context.user is None
        assert context.request is None
        assert context.tags == {}
        assert context.extra == {}
        assert context.server_name is None
        assert context.release is None
        assert context.environment is None


class TestUser:
    """Test cases for User model"""

    def test_user_creation(self):
        """Test creating user"""
        user = User(
            id="123",
            username="testuser",
            email="test@example.com",
            ip_address="192.168.1.1",
            data={"role": "admin"}
        )

        assert user.id == "123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.ip_address == "192.168.1.1"
        assert user.data["role"] == "admin"

    def test_user_defaults(self):
        """Test user default values"""
        user = User()

        assert user.id is None
        assert user.username is None
        assert user.email is None
        assert user.ip_address is None
        assert user.data == {}


class TestRequest:
    """Test cases for Request model"""

    def test_request_creation(self):
        """Test creating request"""
        request = Request(
            url="http://example.com/test",
            method="POST",
            headers={"Content-Type": "application/json"},
            query_string="param=value",
            data='{"key": "value"}',
            env={"REMOTE_ADDR": "192.168.1.1"}
        )

        assert request.url == "http://example.com/test"
        assert request.method == "POST"
        assert request.headers["Content-Type"] == "application/json"
        assert request.query_string == "param=value"
        assert request.data == '{"key": "value"}'
        assert request.env["REMOTE_ADDR"] == "192.168.1.1"

    def test_request_defaults(self):
        """Test request default values"""
        request = Request()

        assert request.url is None
        assert request.method is None
        assert request.headers == {}
        assert request.query_string is None
        assert request.data is None
        assert request.env == {}


class TestBreadcrumb:
    """Test cases for Breadcrumb model"""

    def test_breadcrumb_creation(self):
        """Test creating breadcrumb"""
        timestamp = datetime.now(timezone.utc)
        breadcrumb = Breadcrumb(
            timestamp=timestamp,
            message="Test breadcrumb",
            category="test",
            level=Level.INFO,
            data={"key": "value"},
            type="navigation"
        )

        assert breadcrumb.timestamp == timestamp
        assert breadcrumb.message == "Test breadcrumb"
        assert breadcrumb.category == "test"
        assert breadcrumb.level == Level.INFO
        assert breadcrumb.data["key"] == "value"
        assert breadcrumb.type == "navigation"

    def test_breadcrumb_defaults(self):
        """Test breadcrumb default values"""
        breadcrumb = Breadcrumb(
            timestamp=datetime.now(timezone.utc),
            message="Test breadcrumb"
        )

        assert breadcrumb.category is None
        assert breadcrumb.level is None
        assert breadcrumb.data == {}
        assert breadcrumb.type is None


class TestExceptionInfo:
    """Test cases for ExceptionInfo model"""

    def test_exception_info_creation(self):
        """Test creating exception info"""
        stackframe = StackFrame(
            filename="test.py",
            function="test_func",
            lineno=10
        )

        exception_info = ExceptionInfo(
            type="ValueError",
            value="Test error",
            module="test_module",
            stacktrace=[stackframe]
        )

        assert exception_info.type == "ValueError"
        assert exception_info.value == "Test error"
        assert exception_info.module == "test_module"
        assert len(exception_info.stacktrace) == 1
        assert exception_info.stacktrace[0].filename == "test.py"

    def test_exception_info_defaults(self):
        """Test exception info default values"""
        exception_info = ExceptionInfo(
            type="ValueError",
            value="Test error"
        )

        assert exception_info.module is None
        assert exception_info.stacktrace == []


class TestStackFrame:
    """Test cases for StackFrame model"""

    def test_stackframe_creation(self):
        """Test creating stack frame"""
        frame = StackFrame(
            filename="test.py",
            function="test_func",
            lineno=10,
            colno=5,
            abs_path="/full/path/test.py",
            context_line="print('hello')",
            pre_context=["x = 1", "y = 2"],
            post_context=["z = 3", "return z"],
            in_app=True
        )

        assert frame.filename == "test.py"
        assert frame.function == "test_func"
        assert frame.lineno == 10
        assert frame.colno == 5
        assert frame.abs_path == "/full/path/test.py"
        assert frame.context_line == "print('hello')"
        assert frame.pre_context == ["x = 1", "y = 2"]
        assert frame.post_context == ["z = 3", "return z"]
        assert frame.in_app is True

    def test_stackframe_defaults(self):
        """Test stack frame default values"""
        frame = StackFrame(
            filename="test.py",
            function="test_func",
            lineno=10
        )

        assert frame.colno is None
        assert frame.abs_path is None
        assert frame.context_line is None
        assert frame.pre_context == []
        assert frame.post_context == []
        assert frame.in_app is True


class TestFrameInfoExtraction:
    """Test cases for frame info extraction"""

    def test_get_frame_info_success(self):
        """Test successful frame info extraction"""
        # Create a mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "test.py"
        mock_frame.f_code.co_name = "test_func"
        mock_frame.f_lineno = 10

        with patch("builtins.open", mock_open(read_data="line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\nline11\nline12\n")):
            frame_info = _get_frame_info(mock_frame)

            assert frame_info is not None
            assert frame_info.filename == "test.py"
            assert frame_info.function == "test_func"
            assert frame_info.lineno == 10
            assert frame_info.abs_path == "test.py"
            assert frame_info.context_line == "line10"
            assert len(frame_info.pre_context) == 5
            assert len(frame_info.post_context) == 2

    def test_get_frame_info_file_not_found(self):
        """Test frame info extraction when file is not found"""
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "nonexistent.py"
        mock_frame.f_code.co_name = "test_func"
        mock_frame.f_lineno = 10

        with patch("builtins.open", side_effect=FileNotFoundError):
            frame_info = _get_frame_info(mock_frame)

            assert frame_info is not None
            assert frame_info.filename == "nonexistent.py"
            assert frame_info.function == "test_func"
            assert frame_info.lineno == 10
            assert frame_info.context_line is None
            assert frame_info.pre_context == []
            assert frame_info.post_context == []

    def test_get_frame_info_exception(self):
        """Test frame info extraction when an exception occurs"""
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "test.py"
        mock_frame.f_code.co_name = "test_func"
        mock_frame.f_lineno = 10

        # Simulate an exception during frame info extraction
        with patch.object(mock_frame, '__getattribute__', side_effect=Exception("Test error")):
            frame_info = _get_frame_info(mock_frame)
            assert frame_info is None

    def test_get_frame_info_in_app_detection(self):
        """Test in-app detection for frame info"""
        # Test in-app code
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "/app/src/main.py"
        mock_frame.f_code.co_name = "main_func"
        mock_frame.f_lineno = 10

        with patch("builtins.open", mock_open(read_data="line1\nline2\nline3\n")):
            frame_info = _get_frame_info(mock_frame)
            assert frame_info.in_app is True

        # Test third-party code
        mock_frame.f_code.co_filename = "/usr/lib/python3.9/site-packages/requests/api.py"

        with patch("builtins.open", mock_open(read_data="line1\nline2\nline3\n")):
            frame_info = _get_frame_info(mock_frame)
            assert frame_info.in_app is False
