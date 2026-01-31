"""Comprehensive tests for admin API endpoints."""
import importlib
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer


def _make_session_cookie(*, secret: str, email: str) -> str:
    s = URLSafeSerializer(secret_key=secret, salt="xrayradar-session")
    return s.dumps({"email": email, "ts": 0})


def _set_admin_session(client: TestClient, *, secret: str, email: str) -> None:
    cookie = _make_session_cookie(secret=secret, email=email)
    client.cookies.set("xrayradar_session", cookie)


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
        # Clean up
        db.query(models.TokenProjectAccess).delete()
        db.query(models.Event).delete()
        db.query(models.TokenRequest).delete()
        db.query(models.Token).delete()
        db.query(models.Project).delete()
        db.query(models.User).delete()
        db.commit()

        # Create admin token
        admin_token = models.Token(id=1, name="admin", token="admin", is_admin=True)
        db.add(admin_token)

        # Create test project
        project = models.Project(id=1, name="Test Project")
        db.add(project)

        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))
    return mainmod, client


# ============================================================================
# Token Management Tests
# ============================================================================


def test_admin_create_token_requires_auth(app_and_client):
    """Test that creating a token requires admin authentication."""
    _, client = app_and_client
    r = client.post("/api/admin/tokens", json={"name": "test", "is_admin": False})
    assert r.status_code == 401


def test_admin_create_token_with_session(app_and_client, monkeypatch):
    """Test creating a token with session authentication."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post(
        "/api/admin/tokens",
        json={"name": "test-token", "email": "test@example.com", "is_admin": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "test-token"
    assert data["email"] == "test@example.com"
    assert data["is_admin"] is False
    assert "token" in data
    assert len(data["token"]) > 0
    assert data["id"] is not None


def test_admin_create_token_with_admin_flag(app_and_client, monkeypatch):
    """Test creating an admin token."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post(
        "/api/admin/tokens",
        json={"name": "admin-token", "is_admin": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_admin"] is True


def test_admin_create_token_without_email(app_and_client, monkeypatch):
    """Test creating a token without email."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post(
        "/api/admin/tokens",
        json={"name": "no-email-token", "is_admin": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] is None


def test_admin_list_tokens_requires_auth(app_and_client):
    """Test that listing tokens requires admin authentication."""
    _, client = app_and_client
    r = client.get("/api/admin/tokens")
    assert r.status_code == 401


def test_admin_list_tokens(app_and_client, monkeypatch):
    """Test listing all tokens."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a few tokens
    for i in range(3):
        client.post(
            "/api/admin/tokens",
            json={"name": f"token-{i}", "is_admin": False},
        )

    r = client.get("/api/admin/tokens")
    assert r.status_code == 200
    tokens = r.json()
    assert len(tokens) >= 4  # At least admin + 3 new tokens
    assert all("id" in t for t in tokens)
    assert all("name" in t for t in tokens)
    assert all("is_admin" in t for t in tokens)


def test_admin_revoke_token_requires_auth(app_and_client):
    """Test that revoking a token requires admin authentication."""
    _, client = app_and_client
    r = client.post("/api/admin/tokens/1/revoke")
    assert r.status_code == 401


def test_admin_revoke_token_not_found(app_and_client, monkeypatch):
    """Test revoking a non-existent token."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/999/revoke")
    assert r.status_code == 404


def test_admin_revoke_token(app_and_client, monkeypatch):
    """Test revoking a token."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a token
    r = client.post(
        "/api/admin/tokens",
        json={"name": "to-revoke", "is_admin": False},
    )
    token_id = r.json()["id"]

    # Revoke it
    r = client.post(f"/api/admin/tokens/{token_id}/revoke")
    assert r.status_code == 200
    data = r.json()
    assert data["revoked_at"] is not None

    # Revoking again should be idempotent (no db.add/commit when already revoked)
    first_revoked_at = data["revoked_at"]
    r2 = client.post(f"/api/admin/tokens/{token_id}/revoke")
    assert r2.status_code == 200
    assert r2.json()["revoked_at"] == first_revoked_at  # same timestamp


# ============================================================================
# Project Management Tests
# ============================================================================


def test_admin_list_users_requires_auth(app_and_client):
    """Listing users requires admin auth."""
    _, client = app_and_client
    r = client.get("/api/admin/users")
    assert r.status_code == 401


def test_admin_list_users_empty(app_and_client, monkeypatch):
    """Listing users when none exist returns empty list."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")
    r = client.get("/api/admin/users")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_list_users(app_and_client, monkeypatch):
    """Listing users returns users with plan and event_count."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    db = dbmod.SessionLocal()
    try:
        u = models.User(email="u@example.com", password_hash="h", plan="Free")
        db.add(u)
        db.commit()
        db.refresh(u)
    finally:
        db.close()

    r = client.get("/api/admin/users")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    one = next((x for x in data if x.get("email") == "u@example.com"), None)
    assert one is not None
    assert one["plan"] == "Free"
    assert "event_count" in one


def test_admin_update_user_plan_requires_auth(app_and_client):
    """Updating user plan requires admin auth."""
    _, client = app_and_client
    r = client.patch("/api/admin/users/1/plan", json={"plan": "Pro"})
    assert r.status_code == 401


def test_admin_update_user_plan_not_found(app_and_client, monkeypatch):
    """Updating plan for non-existent user returns 404."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")
    r = client.patch("/api/admin/users/99999/plan", json={"plan": "Pro"})
    assert r.status_code == 404


def test_admin_update_user_plan_invalid_plan(app_and_client, monkeypatch):
    """Updating plan with invalid value returns 400."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    db = dbmod.SessionLocal()
    try:
        u = models.User(email="planuser@example.com", password_hash="h", plan="Free")
        db.add(u)
        db.commit()
        db.refresh(u)
        user_id = u.id
    finally:
        db.close()

    r = client.patch(f"/api/admin/users/{user_id}/plan", json={"plan": "Invalid"})
    assert r.status_code == 400
    assert "invalid" in r.json().get("detail", "").lower()


def test_admin_update_user_plan(app_and_client, monkeypatch):
    """Updating user plan returns updated user with event_count."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    db = dbmod.SessionLocal()
    try:
        u = models.User(email="planupdate@example.com", password_hash="h", plan="Free")
        db.add(u)
        db.commit()
        db.refresh(u)
        user_id = u.id
    finally:
        db.close()

    r = client.patch(f"/api/admin/users/{user_id}/plan", json={"plan": "Pro"})
    assert r.status_code == 200
    data = r.json()
    assert data["plan"] == "Pro"
    assert data["email"] == "planupdate@example.com"
    assert "event_count" in data


def test_admin_list_projects_requires_auth(app_and_client):
    """Test that listing projects requires admin authentication."""
    _, client = app_and_client
    r = client.get("/api/admin/projects")
    assert r.status_code == 401


def test_admin_list_projects(app_and_client, monkeypatch):
    """Test listing all projects."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/projects")
    assert r.status_code == 200
    projects = r.json()
    assert isinstance(projects, list)
    assert len(projects) >= 1
    assert all("id" in p for p in projects)
    assert all("name" in p for p in projects)


# ============================================================================
# Token Project Access Tests
# ============================================================================


def test_admin_grant_project_access_requires_auth(app_and_client):
    """Test that granting project access requires admin authentication."""
    _, client = app_and_client
    r = client.post("/api/admin/tokens/1/projects/1/grant")
    assert r.status_code == 401


def test_admin_grant_project_access_token_not_found(app_and_client, monkeypatch):
    """Test granting access with non-existent token."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/999/projects/1/grant")
    assert r.status_code == 404


def test_admin_grant_project_access_project_not_found(app_and_client, monkeypatch):
    """Test granting access to non-existent project."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/1/projects/999/grant")
    assert r.status_code == 404


def test_admin_grant_project_access(app_and_client, monkeypatch):
    """Test granting project access to a token."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a token
    r = client.post(
        "/api/admin/tokens",
        json={"name": "access-token", "is_admin": False},
    )
    token_id = r.json()["id"]

    # Grant access
    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200
    data = r.json()
    assert data["token_id"] == token_id
    assert data["project_id"] == 1
    assert data["revoked_at"] is None


def test_admin_grant_project_access_regrant_clears_revoked(app_and_client, monkeypatch):
    """Test that regranting access clears revoked_at."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a token
    r = client.post(
        "/api/admin/tokens",
        json={"name": "regrant-token", "is_admin": False},
    )
    token_id = r.json()["id"]

    # Grant access
    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200
    access_id = r.json()["id"]

    # Revoke access
    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/revoke")
    assert r.status_code == 200
    assert r.json()["revoked_at"] is not None

    # Grant again - should clear revoked_at
    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200
    assert r.json()["revoked_at"] is None
    assert r.json()["id"] == access_id  # Should reuse same access record


def test_admin_revoke_project_access_requires_auth(app_and_client):
    """Test that revoking project access requires admin authentication."""
    _, client = app_and_client
    r = client.post("/api/admin/tokens/1/projects/1/revoke")
    assert r.status_code == 401


def test_admin_revoke_project_access_not_found(app_and_client, monkeypatch):
    """Test revoking non-existent project access."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/tokens/1/projects/1/revoke")
    assert r.status_code == 404


def test_admin_revoke_project_access(app_and_client, monkeypatch):
    """Test revoking project access."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a token and grant access
    r = client.post(
        "/api/admin/tokens",
        json={"name": "revoke-token", "is_admin": False},
    )
    token_id = r.json()["id"]

    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200

    # Revoke access
    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/revoke")
    assert r.status_code == 200
    data = r.json()
    assert data["revoked_at"] is not None


def test_admin_list_token_projects_requires_auth(app_and_client):
    """Test that listing token projects requires admin authentication."""
    _, client = app_and_client
    r = client.get("/api/admin/tokens/1/projects")
    assert r.status_code == 401


def test_admin_list_token_projects_empty(app_and_client, monkeypatch):
    """Test listing projects for a token with no access."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a token
    r = client.post(
        "/api/admin/tokens",
        json={"name": "no-access-token", "is_admin": False},
    )
    token_id = r.json()["id"]

    r = client.get(f"/api/admin/tokens/{token_id}/projects")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_list_token_projects(app_and_client, monkeypatch):
    """Test listing projects for a token."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create a project
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        project2 = models.Project(name="Project 2")
        db.add(project2)
        db.commit()
        db.refresh(project2)
        project2_id = project2.id
    finally:
        db.close()

    # Create a token
    r = client.post(
        "/api/admin/tokens",
        json={"name": "multi-access-token", "is_admin": False},
    )
    token_id = r.json()["id"]

    # Grant access to multiple projects
    r = client.post(f"/api/admin/tokens/{token_id}/projects/1/grant")
    assert r.status_code == 200
    r = client.post(f"/api/admin/tokens/{token_id}/projects/{project2_id}/grant")
    assert r.status_code == 200

    # List projects
    r = client.get(f"/api/admin/tokens/{token_id}/projects")
    assert r.status_code == 200
    projects = r.json()
    assert len(projects) == 2
    project_ids = {p["project_id"] for p in projects}
    assert 1 in project_ids
    assert project2_id in project_ids


# ============================================================================
# Event/Log Management Tests
# ============================================================================


def _seed_events(project_id: int, count: int = 5):
    """Helper to create test events."""
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        events = []
        for i in range(count):
            events.append(
                models.Event(
                    project_id=project_id,
                    timestamp=now - timedelta(minutes=i),
                    level=["error", "warning", "info", "debug"][i % 4],
                    message=f"Test message {i}",
                    environment=["production", "staging", "development"][i % 3],
                    release=f"1.{i}.0",
                    server_name=f"server-{i}",
                    payload={"index": i, "data": f"test-{i}"},
                )
            )
        db.add_all(events)
        db.commit()
        for e in events:
            db.refresh(e)
        return events
    finally:
        db.close()


def test_admin_list_project_events_requires_auth(app_and_client):
    """Test that listing project events requires admin authentication."""
    _, client = app_and_client
    r = client.get("/api/admin/projects/1/events")
    assert r.status_code == 401


def test_admin_list_project_events_project_not_found(app_and_client, monkeypatch):
    """Test listing events for non-existent project."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/projects/999/events")
    assert r.status_code == 404


def test_admin_list_project_events_empty(app_and_client, monkeypatch):
    """Test listing events when none exist."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/projects/1/events")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_list_project_events(app_and_client, monkeypatch):
    """Test listing project events."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    events = _seed_events(1, count=5)

    r = client.get("/api/admin/projects/1/events")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    assert all("id" in e for e in data)
    assert all("timestamp" in e for e in data)
    assert all("level" in e for e in data)
    assert all("message" in e for e in data)
    # Payload should not be in list view
    assert all("payload" not in e for e in data)


def test_admin_list_project_events_with_limit(app_and_client, monkeypatch):
    """Test listing events with limit parameter."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=10)

    r = client.get("/api/admin/projects/1/events?limit=3")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_admin_list_project_events_limit_clamped(app_and_client, monkeypatch):
    """Test that limit is clamped to max 200."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=250)

    r = client.get("/api/admin/projects/1/events?limit=500")
    assert r.status_code == 200
    assert len(r.json()) <= 200


def test_admin_list_project_events_with_before(app_and_client, monkeypatch):
    """Test listing events with before timestamp."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    events = _seed_events(1, count=5)
    # Use timestamp of middle event
    before = events[2].timestamp.isoformat()

    r = client.get(f"/api/admin/projects/1/events?before={before}")
    assert r.status_code == 200
    data = r.json()
    assert all(e["timestamp"] < before for e in data)


def test_admin_list_project_events_filter_level(app_and_client, monkeypatch):
    """Test filtering events by level."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=5)

    r = client.get("/api/admin/projects/1/events?level=error")
    assert r.status_code == 200
    data = r.json()
    assert all(e["level"] == "error" for e in data)


def test_admin_list_project_events_filter_environment(app_and_client, monkeypatch):
    """Test filtering events by environment."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=5)

    r = client.get("/api/admin/projects/1/events?environment=production")
    assert r.status_code == 200
    data = r.json()
    assert all(e.get("environment") == "production" for e in data)


def test_admin_list_project_events_filter_release(app_and_client, monkeypatch):
    """Test filtering events by release."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=5)

    r = client.get("/api/admin/projects/1/events?release=1.0.0")
    assert r.status_code == 200
    data = r.json()
    assert all(e.get("release") == "1.0.0" for e in data)


def test_admin_list_project_events_filter_message(app_and_client, monkeypatch):
    """Test filtering events by message substring."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=5)

    r = client.get("/api/admin/projects/1/events?q=message%201")
    assert r.status_code == 200
    data = r.json()
    assert all("message 1" in (e.get("message") or "") for e in data)


def test_admin_list_project_events_combined_filters(app_and_client, monkeypatch):
    """Test combining multiple filters."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    _seed_events(1, count=10)

    r = client.get(
        "/api/admin/projects/1/events?level=error&environment=production&q=message"
    )
    assert r.status_code == 200
    data = r.json()
    assert all(e["level"] == "error" for e in data)
    assert all(e.get("environment") == "production" for e in data)
    assert all("message" in (e.get("message") or "") for e in data)


def test_admin_get_project_event_requires_auth(app_and_client):
    """Test that getting event detail requires admin authentication."""
    _, client = app_and_client
    event_id = uuid4()
    r = client.get(f"/api/admin/projects/1/events/{event_id}")
    assert r.status_code == 401


def test_admin_get_project_event_not_found(app_and_client, monkeypatch):
    """Test getting non-existent event."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    event_id = uuid4()
    r = client.get(f"/api/admin/projects/1/events/{event_id}")
    assert r.status_code == 404


def test_admin_get_project_event_wrong_project(app_and_client, monkeypatch):
    """Test getting event with wrong project ID."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    events = _seed_events(1, count=1)
    event_id = events[0].id

    r = client.get(f"/api/admin/projects/999/events/{event_id}")
    assert r.status_code == 404


def test_admin_get_project_event(app_and_client, monkeypatch):
    """Test getting event detail."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    events = _seed_events(1, count=1)
    event = events[0]

    r = client.get(f"/api/admin/projects/1/events/{event.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(event.id)
    assert data["project_id"] == 1
    assert data["level"] == event.level
    assert data["message"] == event.message
    assert "payload" in data
    assert isinstance(data["payload"], dict)
    assert data["payload"]["index"] == 0


# ============================================================================
# Token Request Management Tests
# ============================================================================


def test_admin_list_token_requests_requires_auth(app_and_client):
    """Test that listing token requests requires admin authentication."""
    _, client = app_and_client
    r = client.get("/api/admin/token-requests")
    assert r.status_code == 401


def test_admin_list_token_requests_empty(app_and_client, monkeypatch):
    """Test listing token requests when none exist."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/token-requests")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_list_token_requests(app_and_client, monkeypatch):
    """Test listing token requests."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create users and token requests
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user1 = models.User(email="user1@example.com", password_hash="hash", plan="Free")
        user2 = models.User(email="user2@example.com", password_hash="hash", plan="Free")
        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        req1 = models.TokenRequest(
            user_id=user1.id, name="Token 1", note="For production"
        )
        req2 = models.TokenRequest(user_id=user2.id, name="Token 2", note="For staging")
        db.add(req1)
        db.add(req2)
        db.commit()
    finally:
        db.close()

    r = client.get("/api/admin/token-requests")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all("id" in req for req in data)
    assert all("user_email" in req for req in data)
    assert all("name" in req for req in data)
    assert all("note" in req for req in data)
    assert all("created_at" in req for req in data)
    assert all("fulfilled_at" in req for req in data)


def test_admin_list_token_requests_with_fulfilled(app_and_client, monkeypatch):
    """Test listing token requests including fulfilled ones."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create user and requests
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(email="user@example.com", password_hash="hash", plan="Free")
        db.add(user)
        db.commit()
        db.refresh(user)

        token = models.Token(name="fulfilled-token", token="token", user_id=user.id)
        db.add(token)
        db.commit()
        db.refresh(token)

        req1 = models.TokenRequest(user_id=user.id, name="Pending")
        req2 = models.TokenRequest(
            user_id=user.id,
            name="Fulfilled",
            fulfilled_at=datetime.now(timezone.utc),
            fulfilled_token_id=token.id,
        )
        db.add(req1)
        db.add(req2)
        db.commit()
    finally:
        db.close()

    r = client.get("/api/admin/token-requests")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    fulfilled = [req for req in data if req["fulfilled_at"]]
    pending = [req for req in data if not req["fulfilled_at"]]
    assert len(fulfilled) == 1
    assert len(pending) == 1


def test_admin_fulfill_token_request_requires_auth(app_and_client):
    """Test that fulfilling token request requires admin authentication."""
    _, client = app_and_client
    r = client.post("/api/admin/token-requests/1/fulfill")
    assert r.status_code == 401


def test_admin_fulfill_token_request_not_found(app_and_client, monkeypatch):
    """Test fulfilling non-existent token request."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/token-requests/999/fulfill")
    assert r.status_code == 404


def test_admin_fulfill_token_request_already_fulfilled(app_and_client, monkeypatch):
    """Test fulfilling already fulfilled token request."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create user, token, and fulfilled request
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
            name="Already Fulfilled",
            fulfilled_at=datetime.now(timezone.utc),
            fulfilled_token_id=token.id,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        request_id = req.id
    finally:
        db.close()

    r = client.post(f"/api/admin/token-requests/{request_id}/fulfill")
    assert r.status_code == 400
    assert "already fulfilled" in r.json()["detail"].lower()


def test_admin_fulfill_token_request_user_not_found(app_and_client, monkeypatch):
    """Test fulfilling token request when user doesn't exist."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create request with invalid user_id
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        req = models.TokenRequest(user_id=999, name="Invalid User")
        db.add(req)
        db.commit()
        db.refresh(req)
        request_id = req.id
    finally:
        db.close()

    r = client.post(f"/api/admin/token-requests/{request_id}/fulfill")
    assert r.status_code == 404


def test_admin_fulfill_token_request(app_and_client, monkeypatch):
    """Test fulfilling a token request."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    # Create user and token request
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(email="user@example.com", password_hash="hash", plan="Free")
        db.add(user)
        db.commit()
        db.refresh(user)

        req = models.TokenRequest(
            user_id=user.id, name="My Token", note="For production"
        )
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
    assert data["is_admin"] is False
    assert "token" in data
    assert len(data["token"]) > 0
    assert data["id"] is not None

    # Verify request is marked as fulfilled
    db = dbmod.SessionLocal()
    try:
        req = db.get(models.TokenRequest, request_id)
        assert req.fulfilled_at is not None
        assert req.fulfilled_token_id is not None
        assert req.fulfilled_token_id == data["id"]
    finally:
        db.close()


# ============================================================================
# Deletion Request Tests
# ============================================================================


def test_admin_list_deletion_requests_requires_auth(app_and_client):
    """Listing deletion requests requires admin auth."""
    _, client = app_and_client
    r = client.get("/api/admin/deletion-requests")
    assert r.status_code == 401


def test_admin_list_deletion_requests_empty(app_and_client, monkeypatch):
    """Listing deletion requests when none exist."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/api/admin/deletion-requests")
    assert r.status_code == 200
    assert r.json() == []


def test_admin_list_deletion_requests(app_and_client, monkeypatch):
    """Listing deletion requests returns pending requests with user email."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(
            email="delreq@example.com",
            password_hash="hash",
            plan="Free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        dr = models.DeletionRequest(user_id=user.id, reason="Leaving")
        db.add(dr)
        db.commit()
    finally:
        db.close()

    r = client.get("/api/admin/deletion-requests")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["user_email"] == "delreq@example.com"
    assert data[0]["reason"] == "Leaving"
    assert "id" in data[0]
    assert "created_at" in data[0]


def test_admin_fulfill_deletion_request(app_and_client, monkeypatch):
    """Fulfilling a deletion request deletes the user and all their data."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(
            email="todelete@example.com",
            password_hash="hash",
            plan="Free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        proj = models.Project(name="P", owner_user_id=user.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        dr = models.DeletionRequest(user_id=user.id, reason="Bye")
        db.add(dr)
        db.commit()
        db.refresh(dr)
        request_id = dr.id
        user_id = user.id
    finally:
        db.close()

    r = client.post(f"/api/admin/deletion-requests/{request_id}/fulfill")
    assert r.status_code == 200
    assert "deleted" in r.json().get("message", "").lower()

    db = dbmod.SessionLocal()
    try:
        assert db.get(models.User, user_id) is None
        assert db.get(models.DeletionRequest, request_id) is None
    finally:
        db.close()


def test_admin_fulfill_deletion_request_not_found(app_and_client, monkeypatch):
    """Fulfilling non-existent deletion request returns 404."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.post("/api/admin/deletion-requests/99999/fulfill")
    assert r.status_code == 404


def test_admin_fulfill_deletion_request_already_fulfilled(app_and_client, monkeypatch):
    """Fulfilling an already fulfilled request returns 400."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        user = models.User(
            email="alreadyfulfilled@example.com",
            password_hash="hash",
            plan="Free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        dr = models.DeletionRequest(
            user_id=user.id,
            reason="x",
            fulfilled_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(dr)
        db.commit()
        db.refresh(dr)
        request_id = dr.id
    finally:
        db.close()

    r = client.post(f"/api/admin/deletion-requests/{request_id}/fulfill")
    assert r.status_code == 400
    assert "already" in r.json().get("detail", "").lower()


def test_admin_fulfill_deletion_request_cancelled(app_and_client, monkeypatch):
    """Fulfilling a cancelled deletion request returns 400."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    _set_admin_session(client, secret="secret", email="admin@example.com")

    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    db = dbmod.SessionLocal()
    try:
        user = models.User(
            email="cancelledreq@example.com",
            password_hash="hash",
            plan="Free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        dr = models.DeletionRequest(
            user_id=user.id,
            reason="x",
            cancelled_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(dr)
        db.commit()
        db.refresh(dr)
        request_id = dr.id
    finally:
        db.close()

    r = client.post(f"/api/admin/deletion-requests/{request_id}/fulfill")
    assert r.status_code == 400
    assert "cancelled" in r.json().get("detail", "").lower()
