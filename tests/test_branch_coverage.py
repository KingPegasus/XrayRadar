import importlib
import sys

import pytest
from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.testclient import TestClient


@pytest.fixture()
def client_and_db(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)
    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as models

    dbmod.init_db()

    db = dbmod.SessionLocal()
    try:
        project = models.Project(name="p1")
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)

    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))
    return client, dbmod, models, project_id


def test_auth_verify_password_edge_cases():
    from xrayradar_server import auth

    assert auth.verify_password("pw", "not-a-valid-format") is False
    assert auth.verify_password("pw", "other$1$salt$deadbeef") is False
    assert auth.verify_password(
        "pw", "pbkdf2_sha256$notint$salt$deadbeef") is False


def test_auth_session_payload_shape():
    from xrayradar_server import auth

    payload = auth.session_payload_for_email("a@example.com")
    assert payload["email"] == "a@example.com"
    assert isinstance(payload["ts"], int)


def test_require_user_unauthorized_when_user_row_missing(client_and_db, monkeypatch):
    client, _, _, _ = client_and_db

    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    from xrayradar_server.auth import get_session_serializer

    cookie = get_session_serializer().dumps(
        {"email": "missing@example.com", "ts": 1})
    client.cookies.set("xrayradar_user_session", cookie)

    r = client.get("/api/me")
    assert r.status_code == 401


def test_user_auth_invalid_inputs(client_and_db):
    client, _, _, _ = client_and_db

    r = client.post(
        "/auth/signup",
        json={"email": "badexample.com",
              "password": "password1", "plan": "Free"},
    )
    assert r.status_code == 400

    r = client.post(
        "/auth/signup",
        json={"email": "a@example.com",
              "password": "password1", "plan": "Invalid"},
    )
    assert r.status_code == 400

    r = client.post("/auth/login", json={"email": "   ", "password": "pw"})
    assert r.status_code == 400


def test_user_auth_wrong_password_branch(client_and_db):
    client, dbmod, models, _ = client_and_db

    db = dbmod.SessionLocal()
    try:
        from xrayradar_server.auth import hash_password

        row = models.User(
            email="a@example.com",
            password_hash=hash_password("correct"),
            plan="Free",
        )
        db.add(row)
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_auth_bad_signature_cookie_parsing(monkeypatch):
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    from xrayradar_server.auth import get_user_session_email

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", b"xrayradar_user_session=not-a-signed-cookie")],
    }
    request = Request(scope)
    assert get_user_session_email(request) is None


def test_get_session_email_returns_none_when_secret_missing(monkeypatch):
    monkeypatch.delenv("XRAYRADAR_SESSION_SECRET", raising=False)

    from xrayradar_server.auth import get_session_email

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", b"xrayradar_session=some-cookie")],
    }
    request = Request(scope)
    assert get_session_email(request) is None


def test_get_user_session_email_returns_none_when_secret_missing(monkeypatch):
    monkeypatch.delenv("XRAYRADAR_SESSION_SECRET", raising=False)

    from xrayradar_server.auth import get_user_session_email

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", b"xrayradar_user_session=some-cookie")],
    }
    request = Request(scope)
    assert get_user_session_email(request) is None


def test_web_router_uncovered_branches(tmp_path, monkeypatch):
    from xrayradar_server.routers.web import register_web

    web_dist = tmp_path / "dist"
    web_dist.mkdir()

    monkeypatch.setenv("XRAYRADAR_WEB_DIST", str(web_dist))

    app = FastAPI()
    register_web(app)
    client = TestClient(app)

    r = client.get("/")
    assert r.status_code == 404

    r = client.get("/auth/login")
    assert r.status_code == 404

    r = client.get("/assets/foo.js")
    assert r.status_code == 404

    r = client.get("/docs")
    assert r.status_code == 200

    r = client.get("/admin")
    assert r.status_code == 404

    r = client.get("/health")
    assert r.status_code == 404

    r = client.get("//")
    assert r.status_code == 404

    r = client.get("/anything")
    assert r.status_code == 404

    index = web_dist / "index.html"
    index.write_text("<html>ok</html>")

    app2 = FastAPI()
    register_web(app2)
    client2 = TestClient(app2)

    r = client2.get("/")
    assert r.status_code == 200

    r = client2.get("/auth/login")
    assert r.status_code == 404

    r = client2.get("/assets/foo.js")
    assert r.status_code == 404

    r = client2.get("/admin")
    assert r.status_code == 404

    r = client2.get("/some-client-route")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_web_router_should_not_fallback_when_path_is_empty_after_strip(tmp_path, monkeypatch):
    from xrayradar_server.routers.web import register_web

    web_dist = tmp_path / "dist"
    web_dist.mkdir()
    (web_dist / "index.html").write_text("<html>ok</html>")
    monkeypatch.setenv("XRAYRADAR_WEB_DIST", str(web_dist))

    app = FastAPI()
    register_web(app)

    handler = app.exception_handlers[StarletteHTTPException]
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
        }
    )
    response = await handler(request, StarletteHTTPException(status_code=404, detail="Not Found"))
    assert response.status_code == 404
