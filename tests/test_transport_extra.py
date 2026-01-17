import json

import pytest
import requests

from xrayradar.exceptions import InvalidDsnError, TransportError
from xrayradar.transport import HttpTransport, NullTransport


def test_redact_dsn_handles_urlparse_failure(monkeypatch):
    import xrayradar.transport as tmod

    def boom(_):
        raise RuntimeError("bad")

    monkeypatch.setattr(tmod, "urlparse", boom)
    # Avoid calling HttpTransport.__init__ (which would also use urlparse).
    t = HttpTransport.__new__(HttpTransport)
    assert t._redact_dsn("http://x") == "<invalid dsn>"


def test_http_transport_invalid_dsn_format_raises():
    with pytest.raises(InvalidDsnError):
        HttpTransport("not-a-url")


def test_http_transport_failed_to_parse_dsn_wraps(monkeypatch):
    import xrayradar.transport as tmod

    def boom(_):
        raise ValueError("explode")

    monkeypatch.setattr(tmod, "urlparse", boom)
    with pytest.raises(InvalidDsnError) as e:
        HttpTransport("http://localhost/1")
    assert "Failed to parse DSN" in str(e.value)


def test_http_transport_sets_auth_token_header(monkeypatch):
    import xrayradar.transport as tmod

    class FakeSession:
        def __init__(self):
            self.headers = {}
            self.auth = None

        def post(self, *a, **k):
            raise AssertionError("should not post")

    monkeypatch.setenv("XRAYRADAR_AUTH_TOKEN", "tok")
    monkeypatch.setattr(tmod.requests, "Session", FakeSession)

    t = HttpTransport("http://localhost/1")
    assert t.session.headers["X-Xrayradar-Token"] == "tok"


def test_http_transport_oversize_payload_truncates(monkeypatch):
    import xrayradar.transport as tmod

    calls = {}

    class FakeResp:
        status_code = 200
        headers = {}
        text = ""

    class FakeSession:
        def __init__(self):
            self.headers = {}
            self.auth = None

        def post(self, url, data, timeout, verify):
            calls["url"] = url
            calls["data"] = data
            return FakeResp()

    monkeypatch.setattr(tmod.requests, "Session", FakeSession)

    t = HttpTransport("http://localhost/1", max_payload_size=200)
    event = {
        "message": "x" * 2000,
        "exception": {"values": [{"stacktrace": {"frames": [{"a": 1}] * 100}}]},
        "breadcrumbs": [{"m": 1}] * 200,
    }

    t.send_event(event)
    payload = json.loads(calls["data"])
    assert payload["message"].endswith("... (truncated)")
    assert len(payload["exception"]["values"][0]["stacktrace"]["frames"]) == 50
    assert len(payload["breadcrumbs"]) == 100


def test_http_transport_flush_noop(monkeypatch):
    t = HttpTransport("http://localhost/1")
    t.flush(timeout=0.1)


def test_http_transport_parse_dsn_with_port():
    t = HttpTransport("https://example.com:8443/1")
    assert t.server_url == "https://example.com:8443"
    assert t.project_id == "1"


def test_send_event_http_error_without_body(monkeypatch):
    t = HttpTransport("https://example.com/1")

    class DummyResponse:
        status_code = 500
        text = ""
        headers = {}

    monkeypatch.setattr(t.session, "post", lambda *a, **k: DummyResponse())

    with pytest.raises(TransportError) as e:
        t.send_event({"message": "hi"})

    assert "HTTP 500" in str(e.value)


def test_send_event_request_exception(monkeypatch):
    t = HttpTransport("https://example.com/1")

    def boom(*a, **k):
        raise requests.exceptions.RequestException("net")

    monkeypatch.setattr(t.session, "post", boom)

    with pytest.raises(TransportError) as e:
        t.send_event({"message": "hi"})

    assert "Network error" in str(e.value)


def test_null_transport_is_noop():
    t = NullTransport()
    assert t.send_event({"message": "x"}) is None
    assert t.flush(timeout=1.0) is None


def test_parse_dsn_missing_project_id_when_split_empty(monkeypatch):
    # Force the `if not path_parts:` branch (coverage line 103) by returning
    # a path object whose `.strip().split()` returns an empty list.
    import xrayradar.transport as tmod

    class FakePath:
        def strip(self, _chars):
            return self

        def split(self, _sep):
            return []

    class FakeParsed:
        scheme = "https"
        netloc = "example.com"
        hostname = "example.com"
        port = None
        path = FakePath()

    monkeypatch.setattr(tmod, "urlparse", lambda _dsn: FakeParsed())

    with pytest.raises(InvalidDsnError):
        HttpTransport("https://example.com/")


def test_http_transport_encode_error_raises(monkeypatch):
    import xrayradar.transport as tmod

    class FakeSession:
        def __init__(self):
            self.headers = {}
            self.auth = None

        def post(self, *a, **k):
            raise AssertionError("should not post")

    monkeypatch.setattr(tmod.requests, "Session", FakeSession)

    t = HttpTransport("http://localhost/1")

    # Force json.dumps to raise a TypeError.
    monkeypatch.setattr(tmod.json, "dumps", lambda *a, **
                        k: (_ for _ in ()).throw(TypeError("bad")))

    with pytest.raises(TransportError):
        t.send_event({"x": object()})
