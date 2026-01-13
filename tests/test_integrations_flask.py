from types import SimpleNamespace

from xrayradar.client import ErrorTracker
from xrayradar.integrations.flask import FlaskIntegration


def test_flask_integration_captures_exception(monkeypatch):
    captured = {}

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            captured["request"] = request
            captured["tags"] = tags
            return "event-id"

    class DummyFlaskRequest:
        method = "GET"
        path = "/error"
        url = "http://testserver/error"
        remote_addr = "127.0.0.1"
        query_string = b"a=1"
        headers = {"User-Agent": "pytest", "Authorization": "Bearer secret"}
        environ = {"SERVER_PORT": "8000"}
        host = "testserver"

    import xrayradar.integrations.flask as flask_mod

    monkeypatch.setattr(flask_mod, "request", DummyFlaskRequest)

    integration = FlaskIntegration(flask_app=None, client=None)
    integration.client = FakeClient()  # type: ignore[assignment]

    exc = ZeroDivisionError("boom")
    integration._handle_exception(None, exc)

    assert isinstance(captured.get("exc"), ZeroDivisionError)
    assert captured["tags"]["framework"] == "flask"
    assert captured["request"]["url"] == "http://testserver/error"
    assert "Authorization" not in captured["request"]["headers"]
