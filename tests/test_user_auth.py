import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_and_client(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as _models

    dbmod.init_db()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)

    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))
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
