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

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            captured["request"] = request
            captured["tags"] = tags
            return "event-id"

    middleware = GrapheneIntegration(client=FakeClient())

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


def test_graphene_middleware_creates_client_when_missing(monkeypatch):
    import xrayradar.integrations.graphene as graphene_mod

    # Force get_client() to return None.
    monkeypatch.setattr(graphene_mod, "get_client", lambda: None)

    created = {"n": 0}

    class FakeClient:
        def __init__(self, *a, **k):
            created["n"] += 1

        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            raise exc

    monkeypatch.setattr(graphene_mod, "ErrorTracker", FakeClient)

    middleware = graphene_mod.GrapheneIntegration(client=None)
    info = SimpleNamespace(context=None, operation=None)

    def next_(_root, _info, **_kwargs):
        raise ValueError("boom")

    with pytest.raises(ValueError):
        middleware.resolve(next_, None, info)

    assert created["n"] == 1
