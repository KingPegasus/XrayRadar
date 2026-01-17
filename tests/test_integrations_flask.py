import importlib
import sys
from types import SimpleNamespace

import pytest

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


def test_flask_integration_init_app_raises_when_flask_missing(monkeypatch):
    import xrayradar.integrations.flask as flask_mod

    integration = FlaskIntegration(flask_app=None, client=None)
    monkeypatch.setattr(flask_mod, "Flask", None)

    with pytest.raises(ImportError):
        integration.init_app(object(), client=object()
                             )  # type: ignore[arg-type]


def test_flask_integration_init_app_and_request_started_and_teardown(monkeypatch):
    # Provide a fake Flask module + signals so the integration can wire itself.
    class FakeSignal:
        def __init__(self):
            self.connections = []

        def connect(self, handler, app):
            self.connections.append((handler, app))

    got_sig = FakeSignal()
    started_sig = FakeSignal()

    class FakeFlaskApp:
        def __init__(self):
            self._teardown_fns = []

        def teardown_appcontext(self, fn):
            self._teardown_fns.append(fn)
            return fn

    class DummyFlaskRequest:
        method = "GET"
        path = "/x"
        url = "http://testserver/x?a=1"
        remote_addr = "127.0.0.1"
        query_string = b"a=1"
        headers = {"User-Agent": "pytest",
                   "Authorization": "Bearer secret", "X": "1"}
        environ = {"SERVER_PORT": "8000"}
        host = "testserver"

    flask_pkg = SimpleNamespace(Flask=FakeFlaskApp, request=DummyFlaskRequest)
    flask_signals_pkg = SimpleNamespace(
        got_request_exception=got_sig,
        request_started=started_sig,
    )

    monkeypatch.setitem(sys.modules, "flask", flask_pkg)
    monkeypatch.setitem(sys.modules, "flask.signals", flask_signals_pkg)

    import xrayradar.integrations.flask as flask_mod
    importlib.reload(flask_mod)

    captured = {"calls": []}

    class FakeClient:
        def clear_breadcrumbs(self):
            captured["calls"].append("clear_breadcrumbs")

        def add_breadcrumb(self, **kwargs):
            captured["calls"].append(("add_breadcrumb", kwargs))

        def set_context(self, ctx_type, ctx_data):
            captured["calls"].append(("set_context", ctx_type, ctx_data))

        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["calls"].append(
                ("capture_exception", type(exc), request, tags))

    app = flask_mod.Flask()
    integration = flask_mod.FlaskIntegration(
        flask_app=app, client=FakeClient())

    assert len(got_sig.connections) == 1
    assert len(started_sig.connections) == 1
    assert len(app._teardown_fns) == 1

    # Exercise request_started handler.
    integration._handle_request_started(app)
    assert "clear_breadcrumbs" in captured["calls"]
    assert any(c[0] == "add_breadcrumb" for c in captured["calls"]
               if isinstance(c, tuple))
    ctx_calls = [c for c in captured["calls"]
                 if isinstance(c, tuple) and c[0] == "set_context"]
    assert ctx_calls
    _, ctx_type, ctx_data = ctx_calls[-1]
    assert ctx_type == "request"
    assert "Authorization" not in ctx_data["headers"]

    # Exercise teardown handler (lines 56-59) calling _handle_exception.
    app._teardown_fns[0](RuntimeError("boom"))
    assert any(c[0] == "capture_exception" for c in captured["calls"]
               if isinstance(c, tuple))

    # Exercise early return when no client (line 114).
    integration.client = None
    integration._handle_exception(app, RuntimeError("x"))


def test_init_flask_integration_returns_instance(monkeypatch):
    # Ensure wrapper returns integration instance.
    import xrayradar.integrations.flask as flask_mod

    class FakeFlaskApp:
        def teardown_appcontext(self, fn):
            return fn

    # Avoid real signal wiring.
    flask_mod.got_request_exception = SimpleNamespace(
        connect=lambda *a, **k: None)
    flask_mod.request_started = SimpleNamespace(connect=lambda *a, **k: None)
    flask_mod.Flask = FakeFlaskApp

    integration = flask_mod.init_flask_integration(
        FakeFlaskApp(), client=ErrorTracker(debug=True))
    assert isinstance(integration, flask_mod.FlaskIntegration)


def test_flask_handle_request_started_no_request_is_noop(monkeypatch):
    import xrayradar.integrations.flask as flask_mod

    integration = FlaskIntegration(flask_app=None, client=None)
    integration.client = ErrorTracker(debug=True)
    monkeypatch.setattr(flask_mod, "request", None)

    # Should just return without doing anything.
    integration._handle_request_started(None)
