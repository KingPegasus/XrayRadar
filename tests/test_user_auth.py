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
