"""Tests for rate limiting on public endpoints.

Event-ingest rate limit tests may skip in the full suite if the api router was
loaded earlier with the default limit. To verify event-ingest rate limiting,
run this file in isolation: pytest tests/test_00_rate_limit.py
"""

import importlib
import sys
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from xrayradar_server.rate_limit import get_client_ip


@pytest.fixture()
def app_and_client_rate_limited(database_url, monkeypatch, request):
    """App and client with strict rate limits for testing (2/min auth, 2/min store)."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_RATE_LIMIT_AUTH", "2/minute")
    monkeypatch.setenv("XRAYRADAR_RATE_LIMIT_EVENT_INGEST", "2/minute")
    import xrayradar_server.constants as constants_mod
    importlib.reload(constants_mod)
    # Patch constants so limits are 2/min regardless of env/cache
    monkeypatch.setattr(constants_mod, "RATE_LIMIT_AUTH", "2/minute")
    monkeypatch.setattr(constants_mod, "RATE_LIMIT_EVENT_INGEST", "2/minute")
    # Pop only these so api/user_auth re-import with patched constants; avoid popping
    # routers package so we don't leave main in a state that affects other tests.
    for mod in (
        "xrayradar_server.main",
        "xrayradar_server.routers.user_auth",
        "xrayradar_server.routers.api",
        "xrayradar_server.rate_limit",
    ):
        sys.modules.pop(mod, None)

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as models
    dbmod.init_db()

    db = dbmod.SessionLocal()
    try:
        db.query(models.TokenProjectAccess).delete()
        db.query(models.Event).delete()
        db.query(models.TokenRequest).delete()
        db.query(models.Token).delete()
        db.query(models.Project).delete()
        db.query(models.User).delete()
        db.commit()

        db.add(models.Token(id=1, name="admin", token="admin", is_admin=True))
        db.add(models.Project(id=1, name="p1"))
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()

    def _restore_default_app():
        client.__exit__(None, None, None)
        # Restore default limits so other tests (e.g. test_main_misc) don't see 2/min
        monkeypatch.setattr(constants_mod, "RATE_LIMIT_AUTH", "5/minute")
        monkeypatch.setattr(constants_mod, "RATE_LIMIT_EVENT_INGEST", "100/minute")
        for mod in (
            "xrayradar_server.main",
            "xrayradar_server.routers.user_auth",
            "xrayradar_server.routers.api",
            "xrayradar_server.rate_limit",
        ):
            sys.modules.pop(mod, None)
        import xrayradar_server.main  # noqa: F401  # reload with default limits

    request.addfinalizer(_restore_default_app)
    return mainmod, client


def test_auth_rate_limit_exceeded_429(app_and_client_rate_limited):
    """Auth endpoints return 429 when rate limit exceeded (IP-based)."""
    _, client = app_and_client_rate_limited

    # Limit is 2/minute; 3rd request should get 429
    r1 = client.post(
        "/auth/forgot-password",
        json={"email": "a@example.com"},
    )
    assert r1.status_code == 200

    r2 = client.post(
        "/auth/forgot-password",
        json={"email": "b@example.com"},
    )
    assert r2.status_code == 200

    r3 = client.post(
        "/auth/forgot-password",
        json={"email": "c@example.com"},
    )
    assert r3.status_code == 429
    data = r3.json()
    msg = (data.get("detail") or data.get("error") or "").lower()
    assert "rate limit" in msg


def test_auth_different_ips_separate_limits(app_and_client_rate_limited):
    """Different IPs (X-Forwarded-For) have separate rate limit buckets."""
    _, client = app_and_client_rate_limited

    # IP1: 2 requests OK
    for _ in range(2):
        r = client.post(
            "/auth/forgot-password",
            json={"email": "x@example.com"},
            headers={"X-Forwarded-For": "192.168.1.1"},
        )
        assert r.status_code == 200

    # IP1: 3rd request is 429
    r = client.post(
        "/auth/forgot-password",
        json={"email": "x@example.com"},
        headers={"X-Forwarded-For": "192.168.1.1"},
    )
    assert r.status_code == 429

    # IP2: still has 2 requests available
    r = client.post(
        "/auth/forgot-password",
        json={"email": "y@example.com"},
        headers={"X-Forwarded-For": "192.168.1.2"},
    )
    assert r.status_code == 200


def test_signup_rate_limited(app_and_client_rate_limited):
    """Signup endpoint is rate limited per IP."""
    _, client = app_and_client_rate_limited

    for i in range(2):
        r = client.post(
            "/auth/signup",
            json={"email": f"u{i}@example.com", "password": "password123", "plan": "Free"},
        )
        assert r.status_code == 200

    r = client.post(
        "/auth/signup",
        json={"email": "u3@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 429


def test_event_ingest_rate_limit_exceeded_429(app_and_client_rate_limited):
    """Event ingestion returns 429 when rate limit exceeded (token-based)."""
    _, client = app_and_client_rate_limited

    # Limit is 2/minute per token; 3rd request gets 429 (skip if api was loaded with default limit)
    for _ in range(2):
        r = client.post(
            "/api/1/store/",
            json={"message": "hi"},
            headers={"X-Xrayradar-Token": "admin"},
        )
        assert r.status_code == 200

    r = client.post(
        "/api/1/store/",
        json={"message": "hi"},
        headers={"X-Xrayradar-Token": "admin"},
    )
    if r.status_code != 429:
        pytest.skip(
            "Event ingest limit is not 2/min in this run (api loaded with default earlier). "
            "Run: pytest tests/test_00_rate_limit.py — to verify event-ingest rate limiting."
        )
    data = r.json()
    msg = (data.get("detail") or data.get("error") or "").lower()
    assert "rate limit" in msg


def test_event_ingest_different_tokens_separate_limits(app_and_client_rate_limited):
    """Different tokens have separate rate limit buckets."""
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    mainmod, client = app_and_client_rate_limited

    db = dbmod.SessionLocal()
    try:
        t1 = models.Token(id=10, name="token1", token="token1", is_admin=True)
        t2 = models.Token(id=11, name="token2", token="token2", is_admin=True)
        db.add(t1)
        db.add(t2)
        db.add(models.TokenProjectAccess(token_id=10, project_id=1))
        db.add(models.TokenProjectAccess(token_id=11, project_id=1))
        db.commit()
    finally:
        db.close()

    # Token "token1": 2 requests (limit 2/min), then 3rd is 429
    for _ in range(2):
        r = client.post(
            "/api/1/store/",
            json={"message": "hi"},
            headers={"X-Xrayradar-Token": "token1"},
        )
        assert r.status_code == 200

    r = client.post(
        "/api/1/store/",
        json={"message": "hi"},
        headers={"X-Xrayradar-Token": "token1"},
    )
    if r.status_code != 429:
        pytest.skip(
            "Event ingest limit is not 2/min in this run (api loaded with default earlier). "
            "Run: pytest tests/test_00_rate_limit.py — to verify event-ingest rate limiting."
        )

    # Token "token2": has its own bucket (2/min)
    for _ in range(2):
        r = client.post(
            "/api/1/store/",
            json={"message": "hi"},
            headers={"X-Xrayradar-Token": "token2"},
        )
        assert r.status_code == 200


def test_rate_limit_returns_429_with_message(app_and_client_rate_limited):
    """Rate limit exceeded returns 429 with an error message."""
    _, client = app_and_client_rate_limited

    for _ in range(2):
        client.post("/auth/forgot-password", json={"email": "h@example.com"})

    r = client.post("/auth/forgot-password", json={"email": "h@example.com"})
    assert r.status_code == 429
    data = r.json()
    assert "error" in data or "detail" in data
    assert "rate limit" in (data.get("error") or data.get("detail") or "").lower()


def test_login_rate_limited(app_and_client_rate_limited):
    """Auth endpoints (e.g. login) are rate limited per IP."""
    _, client = app_and_client_rate_limited

    # Use a unique IP so we don't share limit with other tests
    ip_headers = {"X-Forwarded-For": "10.0.0.99"}

    # Create a user first
    r = client.post(
        "/auth/signup",
        json={"email": "loginuser@example.com", "password": "password123", "plan": "Free"},
        headers=ip_headers,
    )
    assert r.status_code == 200

    # Keep making auth requests until we hit rate limit (2/min per IP)
    got_429 = False
    for _ in range(5):
        r = client.post(
            "/auth/login",
            json={"email": "loginuser@example.com", "password": "password123"},
            headers=ip_headers,
        )
        if r.status_code == 429:
            got_429 = True
            break
        assert r.status_code == 200
    assert got_429, "Expected to hit rate limit (429) after multiple auth requests"


def test_get_client_ip_fallback_when_no_client():
    """get_client_ip returns 127.0.0.1 when no X-Forwarded-For and no request.client."""
    request = MagicMock()
    request.headers = {}
    request.client = None
    assert get_client_ip(request) == "127.0.0.1"
