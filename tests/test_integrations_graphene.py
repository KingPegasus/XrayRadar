from types import SimpleNamespace

import pytest

from xrayradar.client import ErrorTracker
from xrayradar.integrations.graphene import GrapheneIntegration


class DummyRequest:
    def __init__(self):
        self.method = "POST"
        self.META = {"QUERY_STRING": "a=1", "REMOTE_ADDR": "127.0.0.1"}
        self.headers = {"User-Agent": "pytest"}

    def build_absolute_uri(self):
        return "http://testserver/graphql"


def test_graphene_middleware_captures_exception(monkeypatch):
    captured = {}

    def fake_capture_exception(self, exc, request=None, tags=None, **kwargs):
        captured["exc"] = exc
        captured["request"] = request
        captured["tags"] = tags
        return "event-id"

    monkeypatch.setattr(ErrorTracker, "capture_exception",
                        fake_capture_exception)

    middleware = GrapheneIntegration(client=ErrorTracker(debug=True))

    info = SimpleNamespace(
        context=DummyRequest(),
        operation=SimpleNamespace(operation="mutation"),
    )

    def next_(root, info, **kwargs):
        raise ZeroDivisionError("boom")

    with pytest.raises(ZeroDivisionError):
        middleware.resolve(next_, None, info)

    assert isinstance(captured.get("exc"), ZeroDivisionError)
    assert captured["tags"]["framework"] == "graphene"
    assert captured["tags"]["operation"] == "mutation"
    assert captured["request"]["url"] == "http://testserver/graphql"
