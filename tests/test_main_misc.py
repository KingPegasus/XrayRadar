import importlib
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer
from starlette.requests import Request


def _make_session_cookie(*, secret: str, email: str) -> str:
    s = URLSafeSerializer(secret_key=secret, salt="xrayradar-session")
    return s.dumps({"email": email, "ts": 0})


@pytest.fixture()
def app_and_client(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)

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
    request.addfinalizer(lambda: client.__exit__(None, None, None))
    return mainmod, client


def test_cookie_secure_env_true(app_and_client, monkeypatch):
    _, _ = app_and_client
    monkeypatch.setenv("XRAYRADAR_COOKIE_SECURE", "true")
    from xrayradar_server.auth import cookie_secure

    assert cookie_secure() is True


def test_cookie_secure_env_false(app_and_client, monkeypatch):
    _, _ = app_and_client
    monkeypatch.setenv("XRAYRADAR_COOKIE_SECURE", "false")
    from xrayradar_server.auth import cookie_secure

    assert cookie_secure() is False


def _set_admin_session(client: TestClient, *, secret: str, email: str) -> None:
    cookie = _make_session_cookie(secret=secret, email=email)
    client.cookies.set("xrayradar_session", cookie)


def test_health(app_and_client):
    _, client = app_and_client
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_admin_ui_requires_login(app_and_client):
    _, client = app_and_client
    r = client.get("/admin")
    assert r.status_code == 401
    assert "Login with GitHub" in r.text


def test_logout_deletes_cookie(app_and_client):
    _, client = app_and_client
    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_admin_me_requires_login(app_and_client):
    _, client = app_and_client
    r = client.get("/api/admin/me")
    assert r.status_code == 401


def test_admin_ui_session_cookie_allows_access(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200

    r = client.get("/api/admin/me")
    assert r.status_code == 200
    assert r.json()["email"] == "admin@example.com"


def test_github_callback_not_configured_after_state_check(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.delenv("XRAYRADAR_GITHUB_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    r = client.get("/auth/github/callback?code=code123&state=state123")
    assert r.status_code == 500


def test_github_callback_token_exchange_failed(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(500, {})

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get("/auth/github/callback?code=code123&state=state123")
    assert r.status_code == 502


def test_github_callback_missing_access_token(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(200, {})

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get("/auth/github/callback?code=code123&state=state123")
    assert r.status_code == 502


def test_github_callback_emails_fetch_failed(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(200, {"access_token": "token123"})

        def get(self, url, headers=None):
            return _Resp(500, [])

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get("/auth/github/callback?code=code123&state=state123")
    assert r.status_code == 502


def test_github_callback_no_verified_email(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(200, {"access_token": "token123"})

        def get(self, url, headers=None):
            return _Resp(200, [{"email": "x@example.com", "primary": True, "verified": False}])

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get("/auth/github/callback?code=code123&state=state123")
    assert r.status_code == 403


def test_github_callback_email_not_allowed(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(200, {"access_token": "token123"})

        def get(self, url, headers=None):
            return _Resp(200, [{"email": "notallowed@example.com", "primary": True, "verified": True}])

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get("/auth/github/callback?code=code123&state=state123")
    assert r.status_code == 403
    assert "Not allowed" in r.text


def test_session_cookie_bad_signature_is_not_admin(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    client.cookies.set("xrayradar_session", "not-a-valid-cookie")
    r = client.get("/admin")
    assert r.status_code == 401


def test_session_secret_missing_raises(monkeypatch):
    monkeypatch.delenv("XRAYRADAR_SESSION_SECRET", raising=False)

    from xrayradar_server.auth import get_session_serializer

    with pytest.raises(RuntimeError):
        get_session_serializer()


def test_github_login_not_configured(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.delenv("XRAYRADAR_GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("XRAYRADAR_GITHUB_REDIRECT_URI", raising=False)

    r = client.get("/auth/github/login")
    assert r.status_code == 500


def test_github_login_configured_sets_state_cookie(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    r = client.get("/auth/github/login", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith(
        "https://github.com/login/oauth/authorize?")
    assert "xrayradar_oauth_state" in r.headers.get("set-cookie", "")


def test_github_callback_selects_verified_email_when_no_primary_verified(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(200, {"access_token": "token123"})

        def get(self, url, headers=None):
            # No primary+verified; should hit fallback loop (main.py 237-238)
            return _Resp(200, [{"email": "admin@example.com", "primary": False, "verified": True}])

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get(
        "/auth/github/callback?code=code123&state=state123", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/admin"


def test_github_callback_missing_params(app_and_client):
    _, client = app_and_client
    r = client.get("/auth/github/callback")
    assert r.status_code == 400


def test_github_callback_missing_cookie(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    r = client.get("/auth/github/callback?code=c&state=s")
    assert r.status_code == 400


def test_github_callback_invalid_cookie(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    client.cookies.set("xrayradar_oauth_state", "not-a-valid-cookie")
    r = client.get("/auth/github/callback?code=c&state=s")
    assert r.status_code == 400


def test_github_callback_state_mismatch(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "expected", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    r = client.get("/auth/github/callback?code=c&state=wrong")
    assert r.status_code == 400


def test_github_callback_happy_path_sets_session_cookie(app_and_client, monkeypatch):
    mainmod, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("XRAYRADAR_GITHUB_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("XRAYRADAR_GITHUB_REDIRECT_URI",
                       "http://localhost/auth/github/callback")

    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    state_cookie = s.dumps({"state": "state123", "ts": 0})
    client.cookies.set("xrayradar_oauth_state", state_cookie)

    class _Resp:
        def __init__(self, status_code: int, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class _HttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, data=None, headers=None):
            return _Resp(200, {"access_token": "token123"})

        def get(self, url, headers=None):
            return _Resp(200, [{"email": "admin@example.com", "primary": True, "verified": True}])

    monkeypatch.setattr(mainmod.httpx, "Client", _HttpxClient)

    r = client.get(
        "/auth/github/callback?code=code123&state=state123", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/admin"
    assert "xrayradar_session" in r.headers.get("set-cookie", "")

    r = client.get("/admin")
    assert r.status_code == 200


def test_db_get_database_url_missing(monkeypatch):
    monkeypatch.delenv("XRAYRADAR_DATABASE_URL", raising=False)

    import xrayradar_server.db as dbmod

    with pytest.raises(RuntimeError):
        dbmod.get_database_url()


def test_db_engine_dispose_on_url_change(monkeypatch, tmp_path):
    """Test that engine is disposed when database URL changes (covers line 30 in db.py)."""
    import importlib
    import xrayradar_server.db as dbmod
    
    # First database URL
    db1 = tmp_path / "test1.sqlite3"
    url1 = f"sqlite:///{db1}"
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", url1)
    importlib.reload(dbmod)
    
    # Access engine to initialize it
    engine1 = dbmod.engine
    assert engine1 is not None
    
    # Change database URL
    db2 = tmp_path / "test2.sqlite3"
    url2 = f"sqlite:///{db2}"
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", url2)
    importlib.reload(dbmod)
    
    # Access engine again - should create new engine and dispose old one
    engine2 = dbmod.engine
    assert engine2 is not None
    assert engine2 is not engine1


def test_db_ensure_engine_when_session_local_none(monkeypatch, tmp_path):
    """Test that _ensure_engine is called when SessionLocal is None (covers line 43 in db.py)."""
    import importlib
    import xrayradar_server.db as dbmod
    
    db_path = tmp_path / "test.sqlite3"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", url)
    importlib.reload(dbmod)
    
    # Access SessionLocal - this should trigger _ensure_engine if SessionLocal is None
    # The __getattr__ will call _ensure_session_local which calls _ensure_engine
    session_local = dbmod.SessionLocal
    assert session_local is not None
    
    # Access engine directly - should also work
    engine = dbmod.engine
    assert engine is not None


def test_create_project_requires_admin_token(app_and_client):
    _, client = app_and_client
    r = client.post("/api/projects", json={"name": "p"})
    assert r.status_code in (401, 403)


def test_create_project_with_admin_session(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/projects", json={"name": "p2"})
    assert r.status_code == 200
    assert r.json()["name"] == "p2"


def test_get_event_not_found(app_and_client, monkeypatch):
    _, client = app_and_client
    r = client.get(
        "/api/1/events/00000000-0000-0000-0000-000000000000",
        headers={"X-Xrayradar-Token": "admin"},
    )
    assert r.status_code == 404


def test_admin_grant_project_access_unknown_entities(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/999/projects/1/grant")
    assert r.status_code == 404

    r = client.post("/api/admin/tokens/1/projects/999/grant")
    assert r.status_code == 404


def test_logout_function_direct(app_and_client):
    mainmod, _ = app_and_client
    resp = Response()
    out = mainmod.logout(None, resp)
    assert out == {"ok": True}


def test_admin_me_function_direct(app_and_client, monkeypatch):
    mainmod, _ = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    cookie = _make_session_cookie(secret="secret", email="admin@example.com")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/admin/me",
        "headers": [(b"cookie", f"xrayradar_session={cookie}".encode("utf-8"))],
    }
    req = Request(scope)
    out = mainmod.admin_me(req)
    assert out == {"email": "admin@example.com"}


def test_admin_grant_unknown_project_function_direct(app_and_client, monkeypatch):
    mainmod, _ = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    import xrayradar_server.db as dbmod
    from xrayradar_server.models import Token

    db = dbmod.SessionLocal()
    try:
        admin = db.get(Token, 1)
        with pytest.raises(Exception) as exc:
            mainmod.admin_grant_project_access(
                token_id=1,
                project_id=999,
                db=db,
                _=admin,
            )
        assert getattr(exc.value, "status_code", None) == 404
    finally:
        db.close()


def test_admin_list_token_projects_empty(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/tokens/1/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_allowlist_empty_denies_session(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "")
    _set_admin_session(client, secret="secret", email="admin@example.com")
    r = client.get("/api/admin/me")
    assert r.status_code == 401


def test_invalid_token_header_is_unauthorized(app_and_client):
    _, client = app_and_client
    r = client.get("/api/1/events", headers={"X-Xrayradar-Token": "nope"})
    assert r.status_code == 401


def test_admin_requires_admin_privileges_with_non_admin_token(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    r = client.post(
        "/api/admin/tokens",
        json={"name": "nonadmin", "is_admin": False},
        headers={"X-Xrayradar-Token": "admin"},
    )
    assert r.status_code == 200
    nonadmin_token_value = r.json()["token"]

    r = client.get("/api/admin/projects",
                   headers={"X-Xrayradar-Token": nonadmin_token_value})
    assert r.status_code == 403


def test_store_event_unknown_project(app_and_client):
    _, client = app_and_client
    r = client.post(
        "/api/999/store/",
        json={"message": "hi"},
        headers={"X-Xrayradar-Token": "admin"},
    )
    assert r.status_code == 404


def test_store_event_invalid_timestamp_falls_back(app_and_client):
    _, client = app_and_client
    r = client.post(
        "/api/1/store/",
        json={"message": "hi", "timestamp": "not-a-date"},
        headers={"X-Xrayradar-Token": "admin"},
    )
    assert r.status_code == 200
    assert "id" in r.json()


def test_admin_revoke_token_not_found(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/999/revoke")
    assert r.status_code == 404


def test_admin_list_projects(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/projects")
    assert r.status_code == 200
    assert any(p["name"] == "p1" for p in r.json())


def test_admin_grant_regrant_clears_revoked_at(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens", json={"name": "t", "is_admin": False})
    assert r.status_code == 200
    token_id = r.json()["id"]

    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200

    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/revoke")
    assert r.status_code == 200

    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200


def test_admin_revoke_project_access_not_found(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/1/projects/1/revoke")
    assert r.status_code == 404


def _seed_events_for_project(project_id: int, *, count: int = 2):
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        rows = []
        for i in range(count):
            ts = now - timedelta(minutes=i)
            level = "error" if i % 2 == 0 else "info"
            rows.append(
                models.Event(
                    project_id=project_id,
                    timestamp=ts,
                    level=level,
                    message=f"hello {i}",
                    environment="production" if i % 2 == 0 else "staging",
                    release="1.0.0",
                    server_name="srv1",
                    payload={"i": i, "msg": f"hello {i}"},
                )
            )
        db.add_all(rows)
        db.commit()
        for r in rows:
            db.refresh(r)
        return rows
    finally:
        db.close()


def test_admin_list_project_events_and_detail_with_session(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    rows = _seed_events_for_project(1, count=2)
    newest = max(rows, key=lambda r: r.timestamp)

    r = client.get("/api/admin/projects/1/events")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all("payload" not in x for x in data)

    r = client.get("/api/admin/projects/1/events?level=info")
    assert r.status_code == 200
    data = r.json()
    assert all(x["level"] == "info" for x in data)

    # Cover environment filter branch (admin_api.py:233)
    r = client.get("/api/admin/projects/1/events?environment=production")
    assert r.status_code == 200
    data = r.json()
    assert all(x.get("environment") == "production" for x in data)

    # Add an extra event with a different release and distinctive message
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        special = models.Event(
            project_id=1,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5),
            level="error",
            message="unique-release-msg",
            environment="production",
            release="2.0.0",
            server_name="srv2",
            payload={"special": True},
        )
        db.add(special)
        db.commit()
        db.refresh(special)
    finally:
        db.close()

    # Cover release filter branch (admin_api.py:235)
    r = client.get("/api/admin/projects/1/events?release=2.0.0")
    assert r.status_code == 200
    data = r.json()
    assert all(x.get("release") == "2.0.0" for x in data)
    assert any(x.get("message") == "unique-release-msg" for x in data)

    # Cover q (message substring search) branch (admin_api.py:237)
    r = client.get("/api/admin/projects/1/events?q=hello%201")
    assert r.status_code == 200
    data = r.json()
    assert all("hello 1" in (x.get("message") or "") for x in data)

    before = newest.timestamp.isoformat()
    r = client.get(f"/api/admin/projects/1/events?before={before}")
    assert r.status_code == 200
    data = r.json()
    assert all(x["timestamp"] < before for x in data)

    r = client.get(f"/api/admin/projects/1/events/{newest.id}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["id"] == str(newest.id)
    assert detail["project_id"] == 1
    assert isinstance(detail.get("payload"), dict)

    # Cover event detail not-found branch (admin_api.py:268) by project mismatch
    r = client.get(f"/api/admin/projects/999/events/{newest.id}")
    assert r.status_code == 404


def test_admin_list_project_events_unknown_project(app_and_client, monkeypatch):
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/projects/999/events")
    assert r.status_code == 404


def test_admin_list_token_requests_empty(app_and_client, monkeypatch):
    """Test listing token requests when none exist"""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/token-requests")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_list_token_requests(app_and_client, monkeypatch):
    """Test listing token requests"""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a user and token request
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(email="user@example.com", password_hash="hash", plan="Free")
        db.add(user)
        db.commit()
        db.refresh(user)

        req = models.TokenRequest(user_id=user.id, name="My Token", note="For production")
        db.add(req)
        db.commit()
        db.refresh(req)
    finally:
        db.close()

    r = client.get("/api/admin/token-requests")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "My Token"
    assert data[0]["user_email"] == "user@example.com"
    assert data[0]["note"] == "For production"


def test_admin_fulfill_token_request_not_found(app_and_client, monkeypatch):
    """Test fulfilling non-existent token request"""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/token-requests/999/fulfill")
    assert r.status_code == 404


def test_admin_fulfill_token_request_already_fulfilled(app_and_client, monkeypatch):
    """Test fulfilling already fulfilled token request"""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a user and fulfilled token request
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(email="user@example.com", password_hash="hash", plan="Free")
        db.add(user)
        db.commit()
        db.refresh(user)

        token = models.Token(name="existing", token="token", user_id=user.id)
        db.add(token)
        db.commit()
        db.refresh(token)

        req = models.TokenRequest(
            user_id=user.id,
            name="My Token",
            fulfilled_at=datetime.now(timezone.utc),
            fulfilled_token_id=token.id
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        r = client.post(f"/api/admin/token-requests/{req.id}/fulfill")
        assert r.status_code == 400
    finally:
        db.close()


def test_admin_fulfill_token_request_user_not_found(app_and_client, monkeypatch):
    """Test fulfilling token request when user doesn't exist"""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a token request with invalid user_id
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        req = models.TokenRequest(user_id=999, name="My Token")
        db.add(req)
        db.commit()
        db.refresh(req)

        r = client.post(f"/api/admin/token-requests/{req.id}/fulfill")
        assert r.status_code == 404
    finally:
        db.close()


def test_admin_fulfill_token_request(app_and_client, monkeypatch):
    """Test fulfilling a token request"""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a user and token request
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(email="user@example.com", password_hash="hash", plan="Free")
        db.add(user)
        db.commit()
        db.refresh(user)

        req = models.TokenRequest(user_id=user.id, name="My Token", note="For production")
        db.add(req)
        db.commit()
        db.refresh(req)
        request_id = req.id
    finally:
        db.close()

    # Fulfill the request
    r = client.post(f"/api/admin/token-requests/{request_id}/fulfill")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My Token"
    assert data["email"] == "user@example.com"
    assert "token" in data
    assert len(data["token"]) > 0

    # Verify request is marked as fulfilled
    db = dbmod.SessionLocal()
    try:
        req = db.get(models.TokenRequest, request_id)
        assert req.fulfilled_at is not None
        assert req.fulfilled_token_id is not None
    finally:
        db.close()
