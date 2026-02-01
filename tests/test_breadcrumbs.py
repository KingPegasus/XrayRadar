"""Tests for breadcrumb validation and normalization."""

import pytest

from xrayradar_server.routers.api import (
    MAX_BREADCRUMBS,
    MAX_BREADCRUMB_MESSAGE_LENGTH,
    normalize_breadcrumbs,
)


class TestNormalizeBreadcrumbs:
    """Tests for the normalize_breadcrumbs function."""

    def test_empty_event_returns_unchanged(self):
        """Events without breadcrumbs are returned unchanged."""
        event = {"message": "Test error", "level": "error"}
        result = normalize_breadcrumbs(event)
        assert result == event

    def test_none_breadcrumbs_returns_unchanged(self):
        """Events with None breadcrumbs are returned unchanged."""
        event = {"message": "Test error", "breadcrumbs": None}
        result = normalize_breadcrumbs(event)
        assert result == event

    def test_empty_breadcrumbs_list_returns_unchanged(self):
        """Events with empty breadcrumbs list are returned with empty list."""
        event = {"message": "Test error", "breadcrumbs": []}
        result = normalize_breadcrumbs(event)
        assert result["breadcrumbs"] == []

    def test_limits_to_max_breadcrumbs(self):
        """Breadcrumbs are limited to MAX_BREADCRUMBS most recent entries."""
        # Create more than MAX_BREADCRUMBS
        breadcrumbs = [{"message": f"crumb_{i}"} for i in range(MAX_BREADCRUMBS + 50)]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert len(result["breadcrumbs"]) == MAX_BREADCRUMBS
        # Should keep the LAST (most recent) MAX_BREADCRUMBS
        assert result["breadcrumbs"][0]["message"] == "crumb_50"
        assert result["breadcrumbs"][-1]["message"] == f"crumb_{MAX_BREADCRUMBS + 49}"

    def test_truncates_long_messages(self):
        """Long breadcrumb messages are truncated."""
        long_message = "x" * (MAX_BREADCRUMB_MESSAGE_LENGTH + 100)
        breadcrumbs = [{"message": long_message, "type": "http"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        msg = result["breadcrumbs"][0]["message"]
        assert len(msg) == MAX_BREADCRUMB_MESSAGE_LENGTH
        assert msg.endswith("...")

    def test_preserves_short_messages(self):
        """Short messages are preserved unchanged."""
        short_message = "Short message"
        breadcrumbs = [{"message": short_message}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["message"] == short_message

    def test_adds_default_type(self):
        """Breadcrumbs without type get default type."""
        breadcrumbs = [{"message": "Test crumb"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["type"] == "default"

    def test_adds_default_level(self):
        """Breadcrumbs without level get default level."""
        breadcrumbs = [{"message": "Test crumb"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["level"] == "info"

    def test_preserves_existing_type(self):
        """Existing type values are preserved."""
        breadcrumbs = [{"message": "Test crumb", "type": "http"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["type"] == "http"

    def test_preserves_existing_level(self):
        """Existing level values are preserved."""
        breadcrumbs = [{"message": "Test crumb", "level": "error"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["level"] == "error"

    def test_skips_non_dict_breadcrumbs(self):
        """Non-dict entries in breadcrumbs list are skipped."""
        breadcrumbs = [
            {"message": "Valid crumb"},
            "not a dict",
            123,
            None,
            {"message": "Another valid"},
        ]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert len(result["breadcrumbs"]) == 2
        assert result["breadcrumbs"][0]["message"] == "Valid crumb"
        assert result["breadcrumbs"][1]["message"] == "Another valid"

    def test_preserves_timestamp(self):
        """Timestamp values are preserved."""
        timestamp = "2026-01-27T12:00:00Z"
        breadcrumbs = [{"message": "Test", "timestamp": timestamp}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["timestamp"] == timestamp

    def test_preserves_category(self):
        """Category values are preserved."""
        breadcrumbs = [{"message": "Test", "category": "api"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["category"] == "api"

    def test_preserves_data(self):
        """Data dict values are preserved."""
        data = {"status_code": 200, "duration_ms": 45}
        breadcrumbs = [{"message": "Test", "data": data}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["data"] == data

    def test_does_not_modify_original_event(self):
        """normalize_breadcrumbs returns a new dict, not modifying original."""
        breadcrumbs = [{"message": "Test"}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        # Result should be a different object
        assert result is not event
        # Original should be unchanged
        assert "type" not in event["breadcrumbs"][0]

    def test_handles_empty_string_type(self):
        """Empty string type gets replaced with default."""
        breadcrumbs = [{"message": "Test", "type": ""}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["type"] == "default"

    def test_handles_empty_string_level(self):
        """Empty string level gets replaced with default."""
        breadcrumbs = [{"message": "Test", "level": ""}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert result["breadcrumbs"][0]["level"] == "info"

    def test_non_string_message_not_truncated(self):
        """Non-string messages are not truncated (just preserved)."""
        breadcrumbs = [{"message": 12345}]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        # Non-string message is preserved as-is
        assert result["breadcrumbs"][0]["message"] == 12345

    def test_breadcrumbs_not_list_returns_unchanged(self):
        """Non-list breadcrumbs field returns event unchanged."""
        event = {"message": "Test error", "breadcrumbs": "not a list"}
        result = normalize_breadcrumbs(event)
        assert result == event

    def test_multiple_breadcrumbs_all_normalized(self):
        """Multiple breadcrumbs are all normalized."""
        breadcrumbs = [
            {"message": "First"},
            {"message": "Second", "type": "http", "level": "warning"},
            {"message": "Third"},
        ]
        event = {"message": "Test error", "breadcrumbs": breadcrumbs}
        
        result = normalize_breadcrumbs(event)
        
        assert len(result["breadcrumbs"]) == 3
        # First gets defaults
        assert result["breadcrumbs"][0]["type"] == "default"
        assert result["breadcrumbs"][0]["level"] == "info"
        # Second keeps existing values
        assert result["breadcrumbs"][1]["type"] == "http"
        assert result["breadcrumbs"][1]["level"] == "warning"
        # Third gets defaults
        assert result["breadcrumbs"][2]["type"] == "default"
        assert result["breadcrumbs"][2]["level"] == "info"


class TestBreadcrumbSchema:
    """Tests for BreadcrumbIn schema validation."""

    def test_breadcrumb_defaults(self):
        """BreadcrumbIn has correct defaults."""
        from xrayradar_server.schemas import BreadcrumbIn

        bc = BreadcrumbIn()
        assert bc.timestamp is None
        assert bc.type == "default"
        assert bc.category is None
        assert bc.message is None
        assert bc.level == "info"
        assert bc.data is None

    def test_breadcrumb_with_all_fields(self):
        """BreadcrumbIn accepts all fields."""
        from datetime import datetime, timezone
        from xrayradar_server.schemas import BreadcrumbIn

        ts = datetime.now(timezone.utc)
        bc = BreadcrumbIn(
            timestamp=ts,
            type="http",
            category="api",
            message="GET /api/users",
            level="warning",
            data={"status_code": 200},
        )
        assert bc.timestamp == ts
        assert bc.type == "http"
        assert bc.category == "api"
        assert bc.message == "GET /api/users"
        assert bc.level == "warning"
        assert bc.data == {"status_code": 200}

    def test_event_in_with_breadcrumbs(self):
        """EventIn accepts list of BreadcrumbIn."""
        from xrayradar_server.schemas import EventIn

        event = EventIn(
            level="error",
            message="Test error",
            breadcrumbs=[
                {"type": "http", "message": "Request"},
                {"type": "ui", "message": "Click"},
            ],
        )
        assert len(event.breadcrumbs) == 2
        assert event.breadcrumbs[0].type == "http"
        assert event.breadcrumbs[1].type == "ui"

    def test_event_in_breadcrumbs_optional(self):
        """EventIn breadcrumbs field is optional."""
        from xrayradar_server.schemas import EventIn

        event = EventIn(level="error", message="Test error")
        assert event.breadcrumbs is None
