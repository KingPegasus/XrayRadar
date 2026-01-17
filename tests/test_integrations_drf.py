from types import SimpleNamespace

import pytest

from xrayradar.client import ErrorTracker
from xrayradar.integrations.drf import make_drf_exception_handler


class DummyRequest:
    def __init__(self):
        self.method = "GET"
        self.META = {"QUERY_STRING": "", "REMOTE_ADDR": "127.0.0.1"}
        self.headers = {"User-Agent": "pytest"}

    def build_absolute_uri(self):
        return "http://testserver/api/resource"


def test_drf_exception_handler_reports_5xx(monkeypatch):
    captured = {}

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            captured["request"] = request
            captured["tags"] = tags
            return "event-id"

    def wrapped_handler(exc, context):
        return SimpleNamespace(status_code=500)

    handler = make_drf_exception_handler(
        handler=wrapped_handler, client=FakeClient())

    exc = ValueError("boom")
    resp = handler(exc, {"request": DummyRequest()})

    assert resp.status_code == 500
    assert isinstance(captured.get("exc"), ValueError)
    assert captured["tags"]["framework"] == "drf"
    assert captured["tags"]["http_status"] == "500"
    assert captured["request"]["url"] == "http://testserver/api/resource"


def test_drf_exception_handler_does_not_report_4xx(monkeypatch):
    called = {"count": 0}

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            called["count"] += 1
            return "event-id"

    def wrapped_handler(exc, context):
        return SimpleNamespace(status_code=400)

    handler = make_drf_exception_handler(
        handler=wrapped_handler, client=FakeClient())

    resp = handler(ValueError("boom"), {"request": DummyRequest()})
    assert resp.status_code == 400
    assert called["count"] == 0


def test_drf_exception_handler_reports_unhandled(monkeypatch):
    captured = {}

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            return "event-id"

    def wrapped_handler(exc, context):
        return None

    handler = make_drf_exception_handler(
        handler=wrapped_handler, client=FakeClient())

    resp = handler(RuntimeError("boom"), {"request": DummyRequest()})
    assert resp is None
    assert isinstance(captured.get("exc"), RuntimeError)


def test_drf_exception_handler_raises_when_drf_not_installed(monkeypatch):
    import xrayradar.integrations.drf as drf_mod

    monkeypatch.setattr(drf_mod, "drf_exception_handler", None)
    handler = drf_mod.make_drf_exception_handler(
        handler=None, client=ErrorTracker(debug=True))

    with pytest.raises(ImportError):
        handler(ValueError("x"), {})


def test_drf_exception_handler_uses_default_handler_when_available(monkeypatch):
    import xrayradar.integrations.drf as drf_mod

    calls = {"n": 0}

    def default_handler(exc, context):
        calls["n"] += 1
        return SimpleNamespace(status_code=500)

    monkeypatch.setattr(drf_mod, "drf_exception_handler", default_handler)

    handler = drf_mod.make_drf_exception_handler(
        handler=None, client=ErrorTracker(debug=True))
    resp = handler(ValueError("boom"), {"request": DummyRequest()})
    assert resp.status_code == 500
    assert calls["n"] == 1
