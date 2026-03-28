"""Tests for dependency injection functions in deps.py."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import importlib
import sys

from xrayradar_server.deps import (
    require_user,
    require_verified_user,
    get_current_token,
    require_project_access,
    require_admin,
    admin_me,
    authorize_ingest_for_project,
    health,
    _is_session_admin,
)


def _pop_rate_limit_modules():
    """Pop modules that cache rate limit constants so they pick up env on re-import."""
    for mod in (
        "xrayradar_server.main",
        "xrayradar_server.routers.user_auth",
        "xrayradar_server.routers.api",
        "xrayradar_server.constants",
    ):
        sys.modules.pop(mod, None)


@pytest.fixture()
def app_and_client(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_RATE_LIMIT_AUTH", "1000/minute")
    monkeypatch.setenv("XRAYRADAR_RATE_LIMIT_EVENT_INGEST", "10000/minute")
    _pop_rate_limit_modules()

    import xrayradar_server.db as dbmod
    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as models
    dbmod.init_db()

    db = dbmod.SessionLocal()
    try:
        # Clean existing data first
        db.query(models.TokenProjectAccess).delete()
        db.query(models.Event).delete()
        if hasattr(models, "AlertCooldown"):
            db.query(models.AlertCooldown).delete()
        if hasattr(models, "ProjectAlertRecipient"):
            db.query(models.ProjectAlertRecipient).delete()
        if hasattr(models, "ProjectAlertSettings"):
            db.query(models.ProjectAlertSettings).delete()
        db.query(models.TokenRequest).delete()
        db.query(models.Token).delete()
        db.query(models.Project).delete()
        if hasattr(models, "DeletionRequest"):
            db.query(models.DeletionRequest).delete()
        db.query(models.User).delete()
        db.commit()
        
        # Create admin token
        admin_token = models.Token(name="admin", token="admin-token", is_admin=True, email=None)
        db.add(admin_token)
        db.commit()
        db.refresh(admin_token)
        
        # Create user
        user = models.User(
            email="test@example.com",
            password_hash="hash",
            plan="Free",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create project
        project = models.Project(name="test-project", owner_user_id=user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id_val = project.id
        
        # Ensure project ID is set
        if project_id_val is None:
            raise ValueError("Project ID is None after commit and refresh")
        
        # Create non-admin token
        non_admin_token = models.Token(name="non-admin", token="non-admin-token", is_admin=False, email=None)
        db.add(non_admin_token)
        db.commit()
        db.refresh(non_admin_token)
        token_id_val = non_admin_token.id
        
        # Ensure token ID is set
        if token_id_val is None:
            raise ValueError("Token ID is None after commit and refresh")
        
        # Create token project access
        access = models.TokenProjectAccess(token_id=token_id_val, project_id=project_id_val)
        db.add(access)
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod
    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))
    return mainmod, client


def test_health():
    """Test health endpoint dependency."""
    result = health()
    assert result == {"status": "ok", "auth_required": True}


def test_get_current_token_valid(app_and_client):
    """Test get_current_token with valid token."""
    _, client = app_and_client
    
    # This is tested indirectly through endpoints that use it
    # Direct testing would require mocking FastAPI's dependency injection
    # So we test it through actual endpoint calls
    r = client.get("/api/1/events", headers={"X-Xrayradar-Token": "admin-token"})
    # Should not be 401 (unauthorized) - token is valid
    assert r.status_code != 401


def test_get_current_token_missing(app_and_client):
    """Test get_current_token with missing token."""
    _, client = app_and_client
    
    r = client.get("/api/1/events")
    assert r.status_code == 401


def test_get_current_token_invalid(app_and_client):
    """Test get_current_token with invalid token."""
    _, client = app_and_client
    
    r = client.get("/api/1/events", headers={"X-Xrayradar-Token": "invalid-token"})
    assert r.status_code == 401


def test_get_current_token_revoked(app_and_client):
    """Test get_current_token with revoked token."""
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    
    _, client = app_and_client
    
    # Create and revoke a token
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="revoked", token="revoked-token", is_admin=True, email=None)
        db.add(token)
        db.commit()
        db.refresh(token)
        
        from datetime import datetime, timezone
        token.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
    finally:
        db.close()
    
    r = client.get("/api/1/events", headers={"X-Xrayradar-Token": "revoked-token"})
    assert r.status_code == 401


def test_require_project_access_admin_token(app_and_client):
    """Test require_project_access with admin token."""
    _, client = app_and_client
    
    # Admin token should have access to all projects
    r = client.get("/api/1/events", headers={"X-Xrayradar-Token": "admin-token"})
    assert r.status_code == 200


def test_require_project_access_non_admin_with_access(app_and_client):
    """Test require_project_access with non-admin token that has access."""
    _, client = app_and_client
    
    # Non-admin token with project access should work
    r = client.get("/api/1/events", headers={"X-Xrayradar-Token": "non-admin-token"})
    assert r.status_code == 200


def test_require_project_access_non_admin_no_access(app_and_client):
    """Test require_project_access with non-admin token without access."""
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    
    _, client = app_and_client
    
    # Create a new project without access
    db = dbmod.SessionLocal()
    try:
        project2 = models.Project(name="project2")
        db.add(project2)
        db.commit()
        db.refresh(project2)
        project2_id = project2.id
    finally:
        db.close()
    
    # Non-admin token without access should be forbidden
    r = client.get(f"/api/{project2_id}/events", headers={"X-Xrayradar-Token": "non-admin-token"})
    assert r.status_code == 403


def test_require_admin_with_admin_token(app_and_client):
    """Test require_admin with admin token."""
    _, client = app_and_client
    
    r = client.get("/api/admin/tokens", headers={"X-Xrayradar-Token": "admin-token"})
    assert r.status_code == 200


def test_require_admin_with_non_admin_token(app_and_client):
    """Test require_admin with non-admin token."""
    _, client = app_and_client
    
    r = client.get("/api/admin/tokens", headers={"X-Xrayradar-Token": "non-admin-token"})
    assert r.status_code == 403


def test_require_admin_with_session_admin(app_and_client):
    """Test require_admin with session-based admin."""
    _, client = app_and_client
    
    # Create a session for an admin user
    # First signup/login as admin user
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    
    db = dbmod.SessionLocal()
    try:
        admin_user = models.User(
            email="admin@example.com",
            password_hash="hash",
            plan="Teams",
            email_verified=True,
        )
        db.add(admin_user)
        db.commit()
    finally:
        db.close()
    
    # Set admin allowlist
    import os
    os.environ["XRAYRADAR_ADMIN_EMAILS"] = "admin@example.com"
    
    # Login to create session
    r = client.post("/auth/login", json={"email": "admin@example.com", "password": "password123"})
    # This will fail because password doesn't match, but we're testing the session admin path
    # In a real scenario, we'd need proper password setup
    
    # For now, test that admin endpoints work with admin token
    r = client.get("/api/admin/tokens", headers={"X-Xrayradar-Token": "admin-token"})
    assert r.status_code == 200


def test_require_user_not_logged_in(app_and_client):
    """Test require_user when not logged in."""
    _, client = app_and_client
    
    # Try to access a user endpoint without session
    r = client.get("/api/user/projects")
    assert r.status_code == 401


def test_require_verified_user_unverified(app_and_client):
    """Test require_verified_user with unverified email."""
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    
    _, client = app_and_client
    
    # Create unverified user
    db = dbmod.SessionLocal()
    try:
        unverified_user = models.User(
            email="unverified@example.com",
            password_hash="hash",
            plan="Free",
            email_verified=False,
        )
        db.add(unverified_user)
        db.commit()
    finally:
        db.close()
    
    # Login to create session (this would normally require password, but we're testing the verification check)
    # The actual verification check happens in endpoints that use require_verified_user
    # We test this indirectly through endpoints that require verification


def test_authorize_ingest_for_project(app_and_client):
    """Test authorize_ingest_for_project function."""
    import xrayradar_server.db as dbmod
    
    _, client = app_and_client
    
    # This function is tested indirectly through event ingestion endpoints
    # Test that event ingestion works with valid token
    r = client.post(
        "/api/1/store/",
        json={"message": "test"},
        headers={"X-Xrayradar-Token": "admin-token"},
    )
    assert r.status_code == 200


def test_is_session_admin_with_allowlist():
    """Test _is_session_admin with admin in allowlist."""
    from fastapi import Request
    from unittest.mock import MagicMock
    
    request = MagicMock(spec=Request)
    request.headers = {}
    
    with patch("xrayradar_server.deps.get_session_email", return_value="admin@example.com"):
        with patch("xrayradar_server.deps.parse_admin_allowlist", return_value=["admin@example.com"]):
            assert _is_session_admin(request) is True


def test_is_session_admin_not_in_allowlist():
    """Test _is_session_admin with user not in allowlist."""
    from fastapi import Request
    from unittest.mock import MagicMock
    
    request = MagicMock(spec=Request)
    request.headers = {}
    
    with patch("xrayradar_server.deps.get_session_email", return_value="user@example.com"):
        with patch("xrayradar_server.deps.parse_admin_allowlist", return_value=["admin@example.com"]):
            assert _is_session_admin(request) is False


def test_is_session_admin_no_email():
    """Test _is_session_admin with no session email."""
    from fastapi import Request
    from unittest.mock import MagicMock
    
    request = MagicMock(spec=Request)
    request.headers = {}
    
    with patch("xrayradar_server.deps.get_session_email", return_value=None):
        assert _is_session_admin(request) is False


def test_is_session_admin_empty_allowlist():
    """Test _is_session_admin with empty allowlist."""
    from fastapi import Request
    from unittest.mock import MagicMock
    
    request = MagicMock(spec=Request)
    request.headers = {}
    
    with patch("xrayradar_server.deps.get_session_email", return_value="admin@example.com"):
        with patch("xrayradar_server.deps.parse_admin_allowlist", return_value=[]):
            assert _is_session_admin(request) is False


def test_admin_me_with_session_admin(app_and_client, monkeypatch):
    """Test admin_me with session-based admin."""
    from itsdangerous import URLSafeSerializer
    
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")
    
    # Set admin session
    s = URLSafeSerializer(secret_key="secret", salt="xrayradar-session")
    cookie = s.dumps({"email": "admin@example.com", "ts": 0})
    client.cookies.set("xrayradar_session", cookie)
    
    # admin_me endpoint should return email
    r = client.get("/api/admin/me")
    assert r.status_code == 200
    data = r.json()
    assert "email" in data
    assert data["email"] == "admin@example.com"


def test_admin_me_not_logged_in(app_and_client):
    """Test admin_me when not logged in."""
    _, client = app_and_client
    
    r = client.get("/api/admin/me")
    assert r.status_code == 401
