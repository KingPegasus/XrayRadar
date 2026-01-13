from types import SimpleNamespace

from xrayradar.client import ErrorTracker
from xrayradar.integrations import django as django_mod
from xrayradar.integrations.django import DjangoIntegration, init_django_integration


def test_django_integration_captures_exception(monkeypatch):
    captured = {}

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            captured["request"] = request
            captured["tags"] = tags
            return "event-id"

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

    client = FakeClient()
    integration = DjangoIntegration(client)  # type: ignore[arg-type]

    exc = ValueError("boom")
    integration._handle_exception(
        None, exception=exc, request=DummyDjangoRequest())

    assert isinstance(captured.get("exc"), ValueError)
    assert captured["tags"]["framework"] == "django"
    assert captured["request"]["url"] == "http://testserver/graphql"
    assert "Authorization" not in captured["request"]["headers"]


def test_django_integration_sets_up_signal_handlers_when_signals_present(monkeypatch):
    connections = []

    class FakeSignal:
        def connect(self, handler, sender=None):
            connections.append((self, handler, sender))

    monkeypatch.setattr(django_mod, "got_request_exception", FakeSignal())
    monkeypatch.setattr(django_mod, "request_started", FakeSignal())

    integration = DjangoIntegration(client=object())  # type: ignore[arg-type]
    assert integration is not None
    assert len(connections) == 2


def test_django_integration_handle_request_started_sets_context_and_user(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.calls = []

        def clear_breadcrumbs(self):
            self.calls.append(("clear_breadcrumbs",))

        def add_breadcrumb(self, **kwargs):
            self.calls.append(("add_breadcrumb", kwargs))

        def set_context(self, context_type, context_data):
            self.calls.append(("set_context", context_type, context_data))

        def set_user(self, **kwargs):
            self.calls.append(("set_user", kwargs))

    class DummyUser:
        is_authenticated = True
        id = 123
        username = "u"
        email = "e@example.com"

    class DummyDjangoRequest:
        method = "GET"
        path = "/x"
        META = {
            "QUERY_STRING": "a=1",
            "REMOTE_ADDR": "127.0.0.1",
            "SERVER_PORT": "8000",
        }
        headers = {"User-Agent": "pytest", "Authorization": "Bearer secret"}
        user = DummyUser()

        def build_absolute_uri(self):
            return "http://testserver/x?a=1"

        def get_host(self):
            return "testserver"

    client = FakeClient()
    integration = DjangoIntegration(client=client)  # type: ignore[arg-type]
    integration._handle_request_started(None, request=DummyDjangoRequest())

    assert ("clear_breadcrumbs",) in client.calls
    assert any(call[0] == "add_breadcrumb" for call in client.calls)
    assert any(call[0] == "set_context" and call[1]
               == "request" for call in client.calls)
    assert any(call[0] == "set_user" for call in client.calls)


def test_django_integration_handle_request_started_no_request_is_noop():
    calls = []

    class FakeClient:
        def clear_breadcrumbs(self):
            calls.append("clear_breadcrumbs")

        def add_breadcrumb(self, **kwargs):
            calls.append("add_breadcrumb")

        def set_context(self, context_type, context_data):
            calls.append("set_context")

        def set_user(self, **kwargs):
            calls.append("set_user")

    integration = DjangoIntegration(
        client=FakeClient())  # type: ignore[arg-type]
    integration._handle_request_started(None)

    assert calls == ["clear_breadcrumbs"]


def test_django_get_client_ip_prefers_x_forwarded_for():
    integration = DjangoIntegration(client=object())  # type: ignore[arg-type]

    req = SimpleNamespace(META={"HTTP_X_FORWARDED_FOR": "1.2.3.4, 5.6.7.8"})
    assert integration._get_client_ip(req) == "1.2.3.4"

    req2 = SimpleNamespace(META={"REMOTE_ADDR": "9.9.9.9"})
    assert integration._get_client_ip(req2) == "9.9.9.9"

    req3 = SimpleNamespace(META={})
    assert integration._get_client_ip(req3) == "unknown"


def test_django_middleware_process_exception_captures_and_flushes(monkeypatch):
    captured = {}

    class FakeIntegration:
        def __init__(self, client):
            self.client = client

        def _get_client_ip(self, request):
            return "127.0.0.1"

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            captured["request"] = request
            captured["tags"] = tags

        def flush(self, timeout=None):
            captured["flushed"] = timeout

    monkeypatch.setattr(django_mod, "get_client", lambda: FakeClient())
    monkeypatch.setattr(django_mod, "DjangoIntegration", FakeIntegration)

    middleware = django_mod.ErrorTrackerMiddleware(lambda req: "ok")

    class DummyReq:
        method = "GET"
        META = {"QUERY_STRING": "a=1"}
        headers = {"Authorization": "x", "User-Agent": "pytest"}

        def build_absolute_uri(self):
            return "http://testserver/path"

    middleware.process_exception(DummyReq(), ValueError("boom"))
    assert isinstance(captured.get("exc"), ValueError)
    assert captured["tags"]["framework"] == "django"
    assert captured["request"]["url"] == "http://testserver/path"
    assert "Authorization" not in captured["request"]["headers"]
    assert captured["flushed"] == 1.0


def test_init_django_integration_returns_instance(monkeypatch):
    integration = init_django_integration(client=object())
    assert isinstance(integration, DjangoIntegration)
