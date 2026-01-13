from types import SimpleNamespace

from xrayradar.client import ErrorTracker
from xrayradar.integrations.django import DjangoIntegration


def test_django_integration_captures_exception(monkeypatch):
    captured = {}

    def fake_capture_exception(self, exc, request=None, tags=None, **kwargs):
        captured["exc"] = exc
        captured["request"] = request
        captured["tags"] = tags
        return "event-id"

    monkeypatch.setattr(ErrorTracker, "capture_exception",
                        fake_capture_exception)

    class DummyDjangoRequest:
        method = "GET"
        path = "/graphql/"
        META = {"QUERY_STRING": "a=1",
                "REMOTE_ADDR": "127.0.0.1", "SERVER_PORT": "8000"}
        headers = {"User-Agent": "pytest", "Authorization": "Bearer secret"}

        def build_absolute_uri(self):
            return "http://testserver/graphql"

        def get_host(self):
            return "testserver"

        user = SimpleNamespace(is_authenticated=False)

    client = ErrorTracker(debug=True)
    integration = DjangoIntegration(client)

    exc = ValueError("boom")
    integration._handle_exception(
        None, exception=exc, request=DummyDjangoRequest())

    assert isinstance(captured.get("exc"), ValueError)
    assert captured["tags"]["framework"] == "django"
    assert captured["request"]["url"] == "http://testserver/graphql"
    assert "Authorization" not in captured["request"]["headers"]
