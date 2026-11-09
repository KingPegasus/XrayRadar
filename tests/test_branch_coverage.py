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
    assert r.status_code == 200
    assert r.json() is None


def test_user_auth_invalid_inputs(client_and_db):
    client, _, _, _ = client_and_db
    # Use a unique IP so rate limit from test_00_rate_limit (2/min) does not cause 429
    headers = {"X-Forwarded-For": "10.3.0.1"}

    r = client.post(
        "/auth/signup",
        json={"email": "badexample.com",
              "password": "password1", "plan": "Free"},
        headers=headers,
    )
    assert r.status_code == 400

    r = client.post(
        "/auth/signup",
        json={"email": "a@example.com",
              "password": "password1", "plan": "Invalid"},
        headers=headers,
    )
    assert r.status_code == 400

    r = client.post("/auth/login", json={"email": "   ", "password": "pw"}, headers=headers)
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

    # No 404.html (build predates pre-rendered routes): legacy SPA fallback with 200
    r = client2.get("/some-client-route")
    assert r.status_code == 200
    assert "ok" in r.text


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


def test_seo_routes_sitemap_and_redirects(tmp_path, monkeypatch):
    from xrayradar_server.routers.web import register_web
    import xrayradar_server.routers.web as webmod

    web_dist = tmp_path / "dist"
    (web_dist / "privacy").mkdir(parents=True)
    (web_dist / "index.html").write_text("<html>home</html>")
    (web_dist / "404.html").write_text("<html>not found</html>")
    (web_dist / "privacy" / "index.html").write_text("<html>privacy</html>")
    (web_dist / "sitemap.xml").write_text("<urlset></urlset>")
    monkeypatch.setenv("XRAYRADAR_WEB_DIST", str(web_dist))

    original_apps = webmod._registered_apps.copy()
    webmod._registered_apps.clear()
    try:
        app = FastAPI()
        register_web(app, register_catch_all=True)
        client = TestClient(app)

        r = client.get("/sitemap.xml")
        assert r.status_code == 200 and "urlset" in r.text

        r = client.get("/privacy")
        assert r.status_code == 200 and "privacy" in r.text

        r = client.get("/privacy/?a=1", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == "/privacy?a=1"

        r = client.get("/nope")
        assert r.status_code == 404 and "not found" in r.text

        r = client.get("/dashboard/projects/1")
        assert r.status_code == 200 and "home" in r.text
        assert r.headers["x-robots-tag"] == "noindex"

        (web_dist / "dashboard.html").write_text("<html>dash</html>")
        r = client.get("/dashboard/projects/1/issues/ab/events/e.1")
        assert r.status_code == 200 and "dash" in r.text

        # Open-redirect attempts never become redirects
        for evil in ("/%5Cevil.com/", "/%5C%5Cevil.com/", r"/\evil.com/", "/evil.com/", "/a/%2e%2e/"):
            r = client.get(evil, follow_redirects=False)
            assert r.status_code == 404, evil
            assert "location" not in r.headers

        r = client.get("/index.html", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == "/"

        r = client.head("/sitemap.xml")
        assert r.status_code == 200
        r = client.head("/")
        assert r.status_code == 200
        # HEAD to a server path keeps "method not allowed" rather than a 404
        r = client.head("/health")
        assert r.status_code == 405

        # Trailing newline (%0A): Starlette's router drops it before the handler; it
        # must never produce a redirect (header injection) or a non-page response.
        r = client.get("/privacy%0A", follow_redirects=False)
        assert r.status_code in (200, 404)
        assert "location" not in r.headers

        # Legacy section URLs redirect in one hop, even with a trailing slash
        r = client.get("/pricing/", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == "/#pricing"

        # Mixed-case page names redirect to lowercase (same result on every OS)
        r = client.get("/Privacy", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == "/privacy"
        r = client.get("/Dashboard/projects/1/issues/ab/events/AbC", follow_redirects=False)
        assert r.status_code == 301
        assert r.headers["location"] == "/dashboard/projects/1/issues/ab/events/AbC"
    finally:
        webmod._registered_apps = original_apps
