import json

import pytest

from xrayradar.exceptions import InvalidDsnError, TransportError
from xrayradar.transport import HttpTransport


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
