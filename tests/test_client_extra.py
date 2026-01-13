import sys
import weakref

import pytest

import xrayradar
from xrayradar.client import ErrorTracker, _close_weak_client
from xrayradar.transport import Transport


class DummyTransport(Transport):
    def __init__(self):
        self.sent = []
        self.flushed = []

    def send_event(self, event_data):
        self.sent.append(event_data)

    def flush(self, timeout=None):
        self.flushed.append(timeout)


def test_capture_exception_requires_exception_when_none_in_context():
    t = ErrorTracker(dsn="http://localhost/1", transport=DummyTransport())
    with pytest.raises(ValueError):
        t.capture_exception(None)


def test_capture_exception_before_send_can_drop_event():
    transport = DummyTransport()

    def before_send(event):
        return None

    t = ErrorTracker(dsn="http://localhost/1",
                     transport=transport, before_send=before_send)

    eid = t.capture_exception(ValueError("boom"))
    assert eid is None
    assert transport.sent == []


def test_capture_exception_before_send_exception_is_swallowed(monkeypatch):
    transport = DummyTransport()

    def before_send(event):
        raise RuntimeError("bad callback")

    t = ErrorTracker(dsn="http://localhost/1",
                     transport=transport, before_send=before_send)

    eid = t.capture_exception(ValueError("boom"))
    assert eid is None
    assert transport.sent == []


def test_capture_exception_send_failure_returns_none(monkeypatch):
    class BadTransport(DummyTransport):
        def send_event(self, event_data):
            raise RuntimeError("network")

    t = ErrorTracker(dsn="http://localhost/1", transport=BadTransport())
    eid = t.capture_exception(ValueError("boom"))
    assert eid is None


def test_capture_message_fingerprint_and_extra_context():
    transport = DummyTransport()
    t = ErrorTracker(dsn="http://localhost/1", transport=transport)

    eid = t.capture_message("hello", foo="bar")
    assert isinstance(eid, str)
    assert len(transport.sent) == 1
    payload = transport.sent[0]
    assert payload["fingerprint"] == ["hello"]
    assert payload["contexts"]["extra"]["foo"] == "bar"


def test_add_breadcrumb_respects_max_breadcrumbs():
    transport = DummyTransport()
    t = ErrorTracker(dsn="http://localhost/1",
                     transport=transport, max_breadcrumbs=2)

    t.add_breadcrumb("a")
    t.add_breadcrumb("b")
    t.add_breadcrumb("c")

    assert len(t._breadcrumbs) == 2
    assert t._breadcrumbs[0].message == "b"
    assert t._breadcrumbs[1].message == "c"


def test_set_context_user_and_request_and_other():
    transport = DummyTransport()
    t = ErrorTracker(dsn="http://localhost/1", transport=transport)

    t.set_context("user", {"id": "1", "email": "e@e.com"})
    assert t._context.user.id == "1"

    t.set_context("request", {"url": "http://x",
                  "method": "GET", "headers": {}})
    assert t._context.request.url == "http://x"

    t.set_context("custom", {"k": "v"})
    assert t._context.extra["custom"] == {"k": "v"}


def test_flush_calls_transport_flush():
    transport = DummyTransport()
    t = ErrorTracker(dsn="http://localhost/1", transport=transport)

    t.flush(timeout=1.5)
    assert transport.flushed == [1.5]


def test_global_capture_exception_noop_when_no_client_and_no_current_exception(monkeypatch):
    xrayradar.reset_global()
    assert xrayradar.capture_exception() is None


def test_global_capture_exception_swallow_errors(monkeypatch):
    class DummyClient:
        def capture_exception(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(xrayradar.client, "_client", DummyClient())
    assert xrayradar.capture_exception(ValueError("x")) is None


def test_global_excepthook_installed_and_calls_capture(monkeypatch):
    transport = DummyTransport()
    t = ErrorTracker(dsn="http://localhost/1", transport=transport)

    called = {"n": 0}

    def fake_capture(exc, *a, **k):
        called["n"] += 1
        return None

    monkeypatch.setattr(t, "capture_exception", fake_capture)

    t._setup_global_exception_handler()

    # Call excepthook directly so we don't crash the test process.
    sys.excepthook(RuntimeError, RuntimeError("boom"), None)
    assert called["n"] == 1


def test_global_excepthook_ignores_keyboardinterrupt(monkeypatch):
    transport = DummyTransport()
    t = ErrorTracker(dsn="http://localhost/1", transport=transport)

    t._setup_global_exception_handler()

    called = {"n": 0}

    def fake_default(*a, **k):
        called["n"] += 1

    monkeypatch.setattr(sys, "__excepthook__", fake_default)

    sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
    assert called["n"] == 1


def test_close_weak_client_noop_when_dead_ref():
    _close_weak_client(lambda: None)  # type: ignore[arg-type]


def test_close_weak_client_closes_when_alive(monkeypatch):
    called = {"n": 0}

    t = ErrorTracker(debug=True)

    def fake_close():
        called["n"] += 1

    monkeypatch.setattr(t, "close", fake_close)

    _close_weak_client(weakref.ref(t))
    assert called["n"] == 1


def test_sanitize_event_data_send_default_pii_true_returns_same_dict():
    t = ErrorTracker(debug=True, send_default_pii=True)
    payload = {"contexts": {"user": {"email": "a"}}}
    assert t._sanitize_event_data(payload) is payload


def test_sanitize_event_data_strips_user_ip_and_request_details():
    t = ErrorTracker(debug=True, send_default_pii=False)
    payload = {
        "contexts": {
            "user": {"id": "1", "ip_address": "1.1.1.1", "email": "a"},
            "request": {
                "url": "http://x/y?a=1",
                "headers": {"Authorization": "secret", "X": "1"},
                "query_string": "a=1",
                "env": {"REMOTE_ADDR": "1.1.1.1", "Z": "2"},
                "remote_addr": "1.1.1.1",
            },
            "extra": {
                "user": {"id": "2"},
                "request": {
                    "url": "http://x/y?a=1",
                    "headers": {"Cookie": "c", "X": "1"},
                    "query_string": "a=1",
                    "remote_addr": "1.1.1.1",
                },
            },
        }
    }

    out = t._sanitize_event_data(payload)
    assert out is not payload
    assert out["contexts"]["user"].get("ip_address") is None
    assert out["contexts"]["request"]["url"] == "http://x/y"
    assert "Authorization" not in out["contexts"]["request"]["headers"]
    assert out["contexts"]["request"]["query_string"] is None
    assert "REMOTE_ADDR" not in out["contexts"]["request"]["env"]
    assert "user" not in out["contexts"]["extra"]
    assert "Cookie" not in out["contexts"]["extra"]["request"]["headers"]


def test_filter_headers_drops_sensitive_headers():
    t = ErrorTracker(debug=True)
    out = t._filter_headers({"Authorization": "x", "cookie": "y", "X": "1"})
    assert "Authorization" not in out
    assert "cookie" not in out
    assert out["X"] == "1"


def test_generate_fingerprint_exception_with_module_and_stacktrace():
    t = ErrorTracker(debug=True)

    class StackFrame:
        def __init__(self, function):
            self.function = function

    class ExcInfo:
        type = "ValueError"
        module = "m"
        stacktrace = [StackFrame("top")]

    class Ev:
        exception = ExcInfo()
        message = "msg"

    fp = t._generate_fingerprint(Ev())
    assert fp == ["ValueError", "m", "top"]


def test_global_helpers_noop_when_client_none(monkeypatch):
    xrayradar.reset_global()
    xrayradar.add_breadcrumb(message="x")
    xrayradar.set_user(id="1")
    xrayradar.set_tag("a", "b")
    xrayradar.set_extra("k", "v")
