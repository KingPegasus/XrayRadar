import importlib
import sys

import pytest
from fastapi.testclient import TestClient


# Unique IP per fixture so rate limiter bucket is isolated from test_rate_limit (2/min).
_ip_counter = 0


def _unique_auth_ip():
    global _ip_counter
    _ip_counter += 1
    return f"10.1.0.{(_ip_counter % 254) + 1}"


class _ClientWithIP:
    """Wraps TestClient and adds X-Forwarded-For to every request so auth tests get their own rate limit bucket."""

    def __init__(self, client: TestClient, ip: str):
        self._client = client
        self._headers = {"X-Forwarded-For": ip}

    def _merge_headers(self, kwargs):
        headers = dict(self._headers)
        headers.update(kwargs.pop("headers", {}))
        kwargs["headers"] = headers
        return kwargs

    def post(self, url, **kwargs):
        return self._client.post(url, **self._merge_headers(kwargs))

    def get(self, url, **kwargs):
        return self._client.get(url, **self._merge_headers(kwargs))

    def put(self, url, **kwargs):
        return self._client.put(url, **self._merge_headers(kwargs))

    def delete(self, url, **kwargs):
        return self._client.delete(url, **self._merge_headers(kwargs))

    def __getattr__(self, name):
        return getattr(self._client, name)


@pytest.fixture()
def app_and_client(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_RATE_LIMIT_AUTH", "1000/minute")
    monkeypatch.setenv("XRAYRADAR_RATE_LIMIT_EVENT_INGEST", "10000/minute")
    import xrayradar_server.constants as constants_mod
    importlib.reload(constants_mod)
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
    import xrayradar_server.models as _models

    dbmod.init_db()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)

    raw_client = TestClient(mainmod.app)
    raw_client.__enter__()
    request.addfinalizer(lambda: raw_client.__exit__(None, None, None))
    client = _ClientWithIP(raw_client, _unique_auth_ip())
    return mainmod, client


def test_signup_sets_cookie_and_me_works(app_and_client):
    _, client = app_and_client

    r = client.post(
        "/auth/signup",
        json={"email": "u1@example.com",
              "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "u1@example.com"
    assert body["plan"] == "Free"

    r = client.get("/api/me")
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "u1@example.com"


def test_signup_invalid_email_400(app_and_client):
    """Signup with invalid email: empty/min length fails validation (422); invalid format returns 400."""
    _, client = app_and_client
    # Empty/short email fails Pydantic min_length=3 => 422
    r = client.post(
        "/auth/signup",
        json={"email": "", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 422
    # Valid length but no @ => our code returns 400
    r = client.post(
        "/auth/signup",
        json={"email": "no-at-sign", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 400


def test_signup_invalid_plan_400(app_and_client):
    """Signup with invalid plan returns 400."""
    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "u@example.com", "password": "password123", "plan": "Pro"},
    )
    assert r.status_code == 400


def test_signup_duplicate_email_409(app_and_client):
    _, client = app_and_client

    r = client.post(
        "/auth/signup",
        json={"email": "dup@example.com",
              "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post(
        "/auth/signup",
        json={"email": "dup@example.com",
              "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 409


def test_login_invalid_credentials_401(app_and_client):
    _, client = app_and_client

    r = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "password123"},
    )
    assert r.status_code == 401


def test_login_invalid_email_400(app_and_client):
    """Login with empty email fails Pydantic validation => 422."""
    _, client = app_and_client
    r = client.post(
        "/auth/login",
        json={"email": "", "password": "password123"},
    )
    assert r.status_code == 422


def test_login_wrong_password_401(app_and_client):
    """Login with wrong password returns 401."""
    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "wrongpw@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200, f"signup failed: {r.status_code} {r.text}"
    r = client.post(
        "/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


def test_login_after_signup_sets_session(app_and_client):
    _, client = app_and_client

    r = client.post(
        "/auth/signup",
        json={"email": "u2@example.com",
              "password": "password123", "plan": "Basic"},
    )
    assert r.status_code == 200

    client.post("/auth/logout")

    r = client.get("/api/me")
    assert r.status_code == 401

    r = client.post(
        "/auth/login",
        json={"email": "u2@example.com", "password": "password123"},
    )
    assert r.status_code == 200

    r = client.get("/api/me")
    assert r.status_code == 200
    assert r.json()["plan"] == "Basic"


def test_logout_clears_user_session_cookie(app_and_client):
    _, client = app_and_client

    r = client.post(
        "/auth/signup",
        json={"email": "u3@example.com",
              "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/logout")
    assert r.status_code == 200

    r = client.get("/api/me")
    assert r.status_code == 401


def test_verify_email_invalid_token(app_and_client):
    """verify_email returns 400 for missing or short token."""
    _, client = app_and_client
    r = client.get("/auth/verify-email")
    assert r.status_code == 422  # missing query param

    r = client.get("/auth/verify-email?token=short")
    assert r.status_code == 400
    assert "invalid" in r.json().get("detail", "").lower()


def test_verify_email_success(app_and_client):
    """verify_email marks user verified when token matches."""
    from sqlalchemy import select

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "verify@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "verify@example.com")
        ).scalars().first()
        assert u is not None
        token = u.verification_token
        assert token is not None
    finally:
        db.close()

    r = client.get(f"/auth/verify-email?token={token}")
    assert r.status_code == 200
    assert r.json().get("message", "").lower().find("verified") >= 0

    r = client.get("/api/me")
    assert r.status_code == 200
    assert r.json().get("email_verified") is True


def test_verify_email_already_verified(app_and_client):
    """verify_email returns ok when user already verified."""
    from sqlalchemy import select

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "already@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "already@example.com")
        ).scalars().first()
        u.email_verified = True
        token = u.verification_token
        db.add(u)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/auth/verify-email?token={token}")
    assert r.status_code == 200
    assert "already verified" in r.json().get("message", "").lower()


def test_resend_verification_already_verified(app_and_client):
    """resend_verification returns ok when user already verified."""
    from sqlalchemy import select

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "resend@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "resend@example.com")
        ).scalars().first()
        u.email_verified = True
        db.add(u)
        db.commit()
    finally:
        db.close()

    r = client.post("/auth/resend-verification")
    assert r.status_code == 200
    assert "already verified" in r.json().get("message", "").lower()


def test_resend_verification_success(app_and_client):
    """resend_verification returns ok and sends email when user unverified."""
    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "resend2@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/resend-verification")
    assert r.status_code == 200
    assert "sent" in r.json().get("message", "").lower() or "verification" in r.json().get("message", "").lower()


def test_signup_resend_not_configured(app_and_client, monkeypatch):
    """Signup succeeds when Resend is not configured; verification email is skipped."""
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "")
    import xrayradar_server.routers.user_auth as user_auth_mod
    monkeypatch.setattr(user_auth_mod, "RESEND_API_KEY", "")
    monkeypatch.setattr(user_auth_mod, "RESEND_FROM_EMAIL", "")

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "noresend@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "noresend@example.com"


def test_signup_resend_raises_swallowed(app_and_client):
    """When _send_verification_email raises (e.g. Resend API error), signup still succeeds."""
    from unittest.mock import patch, MagicMock

    mock_resend = MagicMock()
    mock_resend.Emails.send = MagicMock(side_effect=RuntimeError("Resend API error"))
    with patch.dict("sys.modules", {"resend": mock_resend}):
        with patch("xrayradar_server.routers.user_auth.RESEND_API_KEY", "key"):
            with patch("xrayradar_server.routers.user_auth.RESEND_FROM_EMAIL", "from@x.com"):
                _, client = app_and_client
                r = client.post(
                    "/auth/signup",
                    json={"email": "resendfail@example.com", "password": "password123", "plan": "Free"},
                )
                assert r.status_code == 200
                assert r.json()["email"] == "resendfail@example.com"


def test_signup_sends_verification_email_success(app_and_client):
    """Signup succeeds when Resend is configured (verification email queued in background)."""
    from unittest.mock import patch

    with patch("xrayradar_server.routers.user_auth.RESEND_API_KEY", "key"):
        with patch("xrayradar_server.routers.user_auth.RESEND_FROM_EMAIL", "from@x.com"):
            _, client = app_and_client
            r = client.post(
                "/auth/signup",
                json={"email": "verifyemail@example.com", "password": "password123", "plan": "Free"},
            )
            assert r.status_code == 200
            assert r.json()["email"] == "verifyemail@example.com"


def test_forgot_password_returns_200_always(app_and_client):
    """forgot_password always returns 200 to avoid email enumeration."""
    _, client = app_and_client
    r = client.post("/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert r.status_code == 200
    assert "ok" in r.json() or "message" in r.json()

    r = client.post("/auth/forgot-password", json={"email": "bad"})
    assert r.status_code == 200


def test_forgot_password_existing_user_sets_token(app_and_client):
    """forgot_password for existing user sets password_reset_token and expires_at."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "reset@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/forgot-password", json={"email": "reset@example.com"})
    assert r.status_code == 200

    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "reset@example.com")
        ).scalars().first()
        assert u is not None
        assert u.password_reset_token is not None
        assert len(u.password_reset_token) >= 10
        assert u.password_reset_expires_at is not None
        assert u.password_reset_expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
    finally:
        db.close()


def test_reset_password_invalid_token_400(app_and_client):
    """reset_password returns 400 for invalid or missing token."""
    _, client = app_and_client
    r = client.post(
        "/auth/reset-password",
        json={"token": "short", "new_password": "newpassword123"},
    )
    assert r.status_code == 422  # Pydantic min_length=10

    r = client.post(
        "/auth/reset-password",
        json={"token": "x" * 32 + "invalid", "new_password": "newpassword123"},
    )
    assert r.status_code == 400
    assert "invalid" in r.json().get("detail", "").lower() or "expired" in r.json().get("detail", "").lower()


def test_reset_password_success(app_and_client):
    """reset_password with valid token updates password; login with new password works."""
    from sqlalchemy import select

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "reset2@example.com", "password": "oldpassword123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/forgot-password", json={"email": "reset2@example.com"})
    assert r.status_code == 200

    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "reset2@example.com")
        ).scalars().first()
        token = u.password_reset_token
        assert token is not None
    finally:
        db.close()

    r = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert r.status_code == 200
    assert "reset" in r.json().get("message", "").lower() or "password" in r.json().get("message", "").lower()

    r = client.post(
        "/auth/login",
        json={"email": "reset2@example.com", "password": "oldpassword123"},
    )
    assert r.status_code == 401

    r = client.post(
        "/auth/login",
        json={"email": "reset2@example.com", "password": "newpassword456"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "reset2@example.com"


def test_reset_password_expired_token(app_and_client):
    """reset_password returns 400 for expired token and clears the token."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "expired@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/forgot-password", json={"email": "expired@example.com"})
    assert r.status_code == 200

    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "expired@example.com")
        ).scalars().first()
        token = u.password_reset_token
        # Set expiry to the past
        u.password_reset_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert r.status_code == 400
    assert "expired" in r.json().get("detail", "").lower() or "invalid" in r.json().get("detail", "").lower()

    # Token should be cleared
    db = dbmod.SessionLocal()
    try:
        u = db.execute(
            select(models.User).where(models.User.email == "expired@example.com")
        ).scalars().first()
        assert u.password_reset_token is None
        assert u.password_reset_expires_at is None
    finally:
        db.close()


def test_verify_email_token_not_found(app_and_client):
    """verify_email returns 400 for valid-length token that doesn't exist."""
    _, client = app_and_client
    # Valid length but non-existent token
    r = client.get("/auth/verify-email?token=" + "x" * 43)
    assert r.status_code == 400
    assert "invalid" in r.json().get("detail", "").lower() or "expired" in r.json().get("detail", "").lower()


def test_forgot_password_sends_email_with_resend(app_and_client):
    """forgot_password returns 200 for existing user (email sent in background when Resend configured)."""
    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "resetemail@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/forgot-password", json={"email": "resetemail@example.com"})
    assert r.status_code == 200
    # Password reset email is queued in background when RESEND_* are set; we assert the handler succeeds


def test_forgot_password_resend_error_swallowed(app_and_client):
    """When Resend raises during forgot_password, error is swallowed."""
    from unittest.mock import patch, MagicMock

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "resenderror@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    mock_resend = MagicMock()
    mock_resend.Emails.send = MagicMock(side_effect=RuntimeError("Resend API error"))
    with patch.dict("sys.modules", {"resend": mock_resend}):
        with patch("xrayradar_server.routers.user_auth.RESEND_API_KEY", "key"):
            with patch("xrayradar_server.routers.user_auth.RESEND_FROM_EMAIL", "from@x.com"):
                r = client.post("/auth/forgot-password", json={"email": "resenderror@example.com"})
                assert r.status_code == 200  # Still returns 200, error is logged


def test_forgot_password_resend_not_configured(app_and_client, monkeypatch):
    """forgot_password skips email when Resend not configured."""
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "")
    import xrayradar_server.routers.user_auth as user_auth_mod
    monkeypatch.setattr(user_auth_mod, "RESEND_API_KEY", "")
    monkeypatch.setattr(user_auth_mod, "RESEND_FROM_EMAIL", "")

    _, client = app_and_client
    r = client.post(
        "/auth/signup",
        json={"email": "noresendreset@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200

    r = client.post("/auth/forgot-password", json={"email": "noresendreset@example.com"})
    assert r.status_code == 200


def test_send_verification_email_resend_configured_success():
    """_send_verification_email calls resend.Emails.send when RESEND is configured (covers 32-54)."""
    from unittest.mock import MagicMock, patch

    import xrayradar_server.routers.user_auth as user_auth_mod

    mock_send = MagicMock(return_value={"id": "msg_123"})
    mock_resend = MagicMock()
    mock_resend.Emails.send = mock_send
    with patch.object(user_auth_mod, "RESEND_API_KEY", "key"):
        with patch.object(user_auth_mod, "RESEND_FROM_EMAIL", "from@test.com"):
            with patch.dict("sys.modules", {"resend": mock_resend}):
                importlib.invalidate_caches()
                user_auth_mod._send_verification_email("user@example.com", "token123")
    mock_send.assert_called_once()
    call_kw = mock_send.call_args[0][0]
    assert call_kw["to"] == ["user@example.com"]
    assert "verify" in call_kw["subject"].lower()
    assert "token123" in call_kw["html"]


def test_send_verification_email_resend_raises_logs_warning():
    """_send_verification_email logs and swallows when resend.Emails.send raises (covers 55-56)."""
    from unittest.mock import MagicMock, patch

    import xrayradar_server.routers.user_auth as user_auth_mod

    mock_resend = MagicMock()
    mock_resend.Emails.send = MagicMock(side_effect=RuntimeError("API error"))
    with patch.object(user_auth_mod, "RESEND_API_KEY", "key"):
        with patch.object(user_auth_mod, "RESEND_FROM_EMAIL", "from@test.com"):
            with patch.dict("sys.modules", {"resend": mock_resend}):
                importlib.invalidate_caches()
                user_auth_mod._send_verification_email("u@example.com", "t")  # no exception


def test_send_password_reset_email_resend_configured_success():
    """_send_password_reset_email calls resend.Emails.send when RESEND is configured (covers 64-86)."""
    from unittest.mock import MagicMock, patch

    import xrayradar_server.routers.user_auth as user_auth_mod

    mock_send = MagicMock(return_value={"id": "msg_456"})
    mock_resend = MagicMock()
    mock_resend.Emails.send = mock_send
    with patch.object(user_auth_mod, "RESEND_API_KEY", "key"):
        with patch.object(user_auth_mod, "RESEND_FROM_EMAIL", "from@test.com"):
            with patch.dict("sys.modules", {"resend": mock_resend}):
                importlib.invalidate_caches()
                user_auth_mod._send_password_reset_email("reset@example.com", "token456")
    mock_send.assert_called_once()
    call_kw = mock_send.call_args[0][0]
    assert call_kw["to"] == ["reset@example.com"]
    assert "reset" in call_kw["subject"].lower()


def test_send_password_reset_email_resend_raises_logs_warning():
    """_send_password_reset_email logs and swallows when resend raises (covers 87-88)."""
    from unittest.mock import MagicMock, patch

    import xrayradar_server.routers.user_auth as user_auth_mod

    mock_resend = MagicMock()
    mock_resend.Emails.send = MagicMock(side_effect=Exception("Network error"))
    with patch.object(user_auth_mod, "RESEND_API_KEY", "key"):
        with patch.object(user_auth_mod, "RESEND_FROM_EMAIL", "from@test.com"):
            with patch.dict("sys.modules", {"resend": mock_resend}):
                importlib.invalidate_caches()
                user_auth_mod._send_password_reset_email("u@example.com", "t")  # no exception
