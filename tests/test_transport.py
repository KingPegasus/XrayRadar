import os

import pytest

from xrayradar.exceptions import InvalidDsnError, RateLimitedError, TransportError
from xrayradar.transport import HttpTransport


class DummyResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text
        self.headers = {}


def test_http_transport_parses_dsn_minimal(monkeypatch):
    monkeypatch.delenv("XRAYRADAR_AUTH_TOKEN", raising=False)
    t = HttpTransport("https://example.com/1")
    assert t.server_url == "https://example.com"
    assert t.project_id == "1"


def test_http_transport_sets_token_header(monkeypatch):
    monkeypatch.setenv("XRAYRADAR_AUTH_TOKEN", "tok")
    t = HttpTransport("https://example.com/1")
    assert t.session.headers["X-Xrayradar-Token"] == "tok"


def test_http_transport_auth_token_argument_overrides_env(monkeypatch):
    monkeypatch.setenv("XRAYRADAR_AUTH_TOKEN", "envtok")
    t = HttpTransport("https://example.com/1", auth_token="argtok")
    assert t.session.headers["X-Xrayradar-Token"] == "argtok"


def test_http_transport_invalid_dsn_raises():
    with pytest.raises(InvalidDsnError):
        HttpTransport("not-a-url")


def test_http_transport_missing_project_id_raises():
    with pytest.raises(InvalidDsnError):
        HttpTransport("https://example.com/")


def test_http_transport_redacts_secret_in_error():
    t = HttpTransport("https://public:secret@example.com/1")
    redacted = t._redact_dsn("https://public:secret@example.com/1")
    assert "secret" not in redacted
    assert redacted.startswith("https://public@")


def test_send_event_rate_limited(monkeypatch):
    t = HttpTransport("https://example.com/1")

    def fake_post(*args, **kwargs):
        r = DummyResponse(status_code=429)
        r.headers = {"Retry-After": "12"}
        return r

    monkeypatch.setattr(t.session, "post", fake_post)

    with pytest.raises(RateLimitedError):
        t.send_event({"message": "hi"})


def test_send_event_http_error_includes_short_body(monkeypatch):
    t = HttpTransport("https://example.com/1")

    def fake_post(*args, **kwargs):
        return DummyResponse(status_code=500, text="x" * 1000)

    monkeypatch.setattr(t.session, "post", fake_post)

    with pytest.raises(TransportError) as e:
        t.send_event({"message": "hi"})

    msg = str(e.value)
    assert "HTTP 500" in msg
    assert len(msg) < 600


def test_send_event_truncates_payload(monkeypatch):
    t = HttpTransport("https://example.com/1", max_payload_size=10)

    def fake_post(*args, **kwargs):
        return DummyResponse(status_code=200)

    monkeypatch.setattr(t.session, "post", fake_post)

    big = {"message": "x" * 5000}
    t.send_event(big)
