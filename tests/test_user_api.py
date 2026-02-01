"""Tests for user API endpoints"""

import importlib
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer
from sqlalchemy import select

from xrayradar_server import models


def _make_session_cookie(*, secret: str, email: str) -> str:
    s = URLSafeSerializer(secret_key=secret, salt="xrayradar-session")
    return s.dumps({"email": email.strip().lower(), "ts": int(datetime.now(timezone.utc).timestamp())})


@pytest.fixture()
def app_and_client_with_user(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as models
    dbmod.init_db()

    db = dbmod.SessionLocal()
    try:
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
        db.add(models.Token(id=1, name="admin", token="admin", is_admin=True))
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))

    # Create user via signup to get proper session cookie
    r = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    user_data = r.json()

    # Mark email verified so require_verified_user endpoints (create project, grant, etc.) succeed
    db = dbmod.SessionLocal()
    try:
        u = db.execute(select(models.User).where(models.User.email == user_data["email"])).scalars().first()
        if u:
            u.email_verified = True
            db.add(u)
            db.commit()
    finally:
        db.close()

    return mainmod, client, {"email": user_data["email"], "id": user_data["id"]}


@pytest.fixture()
def app_and_client_with_unverified_user(database_url, monkeypatch, request):
    """Same as app_and_client_with_user but leaves email_verified=False (for testing 403 on sensitive actions)."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as models
    dbmod.init_db()

    db = dbmod.SessionLocal()
    try:
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

        db.add(models.Token(id=1, name="admin", token="admin", is_admin=True))
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))

    r = client.post(
        "/auth/signup",
        json={"email": "unverified@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    user_data = r.json()
    # Do NOT set email_verified=True
    return mainmod, client, {"email": user_data["email"], "id": user_data["id"]}


def _set_user_session(client: TestClient, *, secret: str, email: str) -> None:
    cookie = _make_session_cookie(secret=secret, email=email)
    client.cookies.set("xrayradar_user_session", cookie, domain="localhost", path="/")


def test_user_list_projects_empty(app_and_client_with_user):
    """Test listing projects when user has none"""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/projects")
    assert r.status_code == 200
    assert r.json() == []


def test_user_create_project(app_and_client_with_user):
    """Test creating a project"""
    mainmod, client, user = app_and_client_with_user

    r = client.post("/api/user/projects", json={"name": "My Project"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My Project"
    assert "id" in data


def test_user_create_project_requires_verified_email(app_and_client_with_unverified_user):
    """Creating a project returns 403 when user email is not verified."""
    mainmod, client, user = app_and_client_with_unverified_user

    r = client.post("/api/user/projects", json={"name": "My Project"})
    assert r.status_code == 403
    assert "verification" in r.json().get("detail", "").lower()


def test_user_list_projects(app_and_client_with_user):
    """Test listing user's projects"""
    mainmod, client, user = app_and_client_with_user

    # Create a project
    r1 = client.post("/api/user/projects", json={"name": "Project 1"})
    assert r1.status_code == 200

    # List projects
    r2 = client.get("/api/user/projects")
    assert r2.status_code == 200
    projects = r2.json()
    assert len(projects) == 1
    assert projects[0]["name"] == "Project 1"


def test_user_list_tokens_empty(app_and_client_with_user):
    """Test listing tokens when user has none"""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/tokens")
    assert r.status_code == 200
    assert r.json() == []


def test_user_list_token_projects_not_found(app_and_client_with_user):
    """Test listing token projects for non-existent token"""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/tokens/999/projects")
    assert r.status_code == 404


def test_user_list_token_projects(app_and_client_with_user):
    """Test listing token projects successfully"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create token
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        # Grant access
        access = models.TokenProjectAccess(token_id=token.id, project_id=project_id)
        db.add(access)
        db.commit()

        # List token projects
        r = client.get(f"/api/user/tokens/{token.id}/projects")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["project_id"] == project_id
    finally:
        db.close()


def test_user_grant_project_access_not_owned_project(app_and_client_with_user):
    """Test granting access fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        # Create a token for the user
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        # Try to grant access to other user's project
        r = client.post(f"/api/user/tokens/{token.id}/projects/{other_project.id}/grant")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_grant_project_access_not_user_token(app_and_client_with_user):
    """Test granting access fails for non-user token"""
    mainmod, client, user = app_and_client_with_user

    # Create user's project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Try to grant access with admin token (not user's token)
    r = client.post(f"/api/user/tokens/1/projects/{project_id}/grant")
    assert r.status_code == 404


def test_user_grant_project_access_revoked_token(app_and_client_with_user):
    """Test granting access fails for revoked token"""
    mainmod, client, user = app_and_client_with_user

    # Create user's project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create and revoke a token
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"], revoked_at=datetime.now(timezone.utc))
        db.add(token)
        db.commit()
        db.refresh(token)

        r = client.post(f"/api/user/tokens/{token.id}/projects/{project_id}/grant")
        assert r.status_code == 400
    finally:
        db.close()


def test_user_grant_project_access(app_and_client_with_user):
    """Test granting project access to token"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create token
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        # Grant access
        r = client.post(f"/api/user/tokens/{token.id}/projects/{project_id}/grant")
        assert r.status_code == 200
        assert r.json()["ok"] is True
    finally:
        db.close()


def test_user_grant_project_access_revoked_access(app_and_client_with_user):
    """Test granting access when access exists but is revoked (covers line 134)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create token and revoked access
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        # Create revoked access
        access = models.TokenProjectAccess(
            token_id=token.id,
            project_id=project_id,
            revoked_at=datetime.now(timezone.utc)
        )
        db.add(access)
        db.commit()

        # Grant access (should unrevoke)
        r = client.post(f"/api/user/tokens/{token.id}/projects/{project_id}/grant")
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # Verify access is no longer revoked
        db.refresh(access)
        assert access.revoked_at is None
    finally:
        db.close()


def test_user_list_token_requests_empty(app_and_client_with_user):
    """Test listing token requests when user has none"""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/token-requests")
    assert r.status_code == 200
    assert r.json() == []


def test_user_create_token_request(app_and_client_with_user):
    """Test creating a token request"""
    mainmod, client, user = app_and_client_with_user

    r = client.post("/api/user/token-requests", json={"name": "My Token", "note": "For production"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My Token"
    assert data["note"] == "For production"
    assert "id" in data


def test_user_create_token_request_no_note(app_and_client_with_user):
    """Test creating a token request without note"""
    mainmod, client, user = app_and_client_with_user

    r = client.post("/api/user/token-requests", json={"name": "My Token"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "My Token"
    assert data["note"] is None


def test_user_list_issues_empty(app_and_client_with_user):
    """Test listing issues when project has none"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/issues")
    assert r.status_code == 200
    assert r.json() == []


def test_user_list_issues_with_events(app_and_client_with_user):
    """Test listing issues with events (covers lines 208-218)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprints
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event1 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 1",
            fingerprint="fp1",
            payload={}
        )
        event2 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 2",
            fingerprint="fp2",
            payload={}
        )
        # Event with same fingerprint
        event3 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 1",
            fingerprint="fp1",
            payload={}
        )
        db.add_all([event1, event2, event3])
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/issues")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2  # Two unique fingerprints
    # Check that counts are correct
    fp1_issue = next((i for i in data if i["fingerprint"] == "fp1"), None)
    assert fp1_issue is not None
    assert fp1_issue["count"] == 2  # Two events with fp1
    assert fp1_issue["first_seen"] is not None
    assert fp1_issue["last_seen"] is not None


def test_user_list_issues_limit_clamping(app_and_client_with_user):
    """Test limit clamping in issues endpoint"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create many events with different fingerprints
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        events = []
        for i in range(15):
            events.append(models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message=f"Test error {i}",
                fingerprint=f"fp{i}",
                payload={}
            ))
        db.add_all(events)
        db.commit()
    finally:
        db.close()

    # Test with limit=0 (should clamp to 1)
    r = client.get(f"/api/user/projects/{project_id}/issues?limit=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1  # Clamped to minimum 1

    # Test with limit=300 (should clamp to 200)
    r = client.get(f"/api/user/projects/{project_id}/issues?limit=300")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 15  # All fingerprints, but limit was clamped to 200


def test_user_list_issues_continue_branch(app_and_client_with_user):
    """Test the continue branch when latest is None (covers line 216-217)
    
    This tests the defensive check where if a fingerprint appears in the aggregation
    but the latest event query returns None, we skip it. We test this by directly
    calling the function with a mocked database session.
    """
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprints
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event1 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error",
            fingerprint="fp1",
            payload={}
        )
        event2 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 2",
            fingerprint="fp2",
            payload={}
        )
        db.add_all([event1, event2])
        db.commit()
        db.refresh(event1)
        db.refresh(event2)
    finally:
        db.close()

    # Test the function directly with a mocked session
    from xrayradar_server.routers import user_api
    from xrayradar_server.models import User
    
    # Get the actual User model instance
    test_db = dbmod.SessionLocal()
    try:
        user_obj = test_db.get(User, user["id"])
        assert user_obj is not None
        
        latest_query_count = [0]
        original_execute = test_db.execute
        
        def mock_execute(statement, *args, **kwargs):
            # Check if this is the latest event query (has limit(1))
            if hasattr(statement, '_limit_clause') and statement._limit_clause is not None:
                # Check if it's filtering by fingerprint
                if hasattr(statement, 'whereclause') and statement.whereclause is not None:
                    latest_query_count[0] += 1
                    if latest_query_count[0] == 2:  # Second query (for fp2)
                        # Return a mock result that yields None
                        mock_result = MagicMock()
                        mock_scalars = MagicMock()
                        mock_scalars.first.return_value = None
                        mock_result.scalars.return_value = mock_scalars
                        return mock_result
            return original_execute(statement, *args, **kwargs)
        
        test_db.execute = mock_execute
        
        # Call the function directly
        result = user_api.user_list_issues(project_id, limit=50, user=user_obj, db=test_db)
        
        # Should only have fp1 (fp2 was skipped due to continue)
        assert len(result) == 1
        assert result[0].fingerprint == "fp1"
    finally:
        test_db.close()


def test_user_list_issue_events(app_and_client_with_user):
    """Test listing issue events (covers lines 245-255)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprint
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event1 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error",
            fingerprint="abc123",
            payload={}
        )
        event2 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error",
            fingerprint="abc123",
            payload={}
        )
        db.add_all([event1, event2])
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/issues/abc123/events")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all(e["level"] == "error" for e in data)
    assert all("id" in e for e in data)


def test_user_list_issue_events_limit_clamping(app_and_client_with_user):
    """Test limit clamping in issue events (covers lines 245-255)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprint
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        events = []
        for i in range(10):
            events.append(models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message=f"Test error {i}",
                fingerprint="abc123",
                payload={}
            ))
        db.add_all(events)
        db.commit()
    finally:
        db.close()

    # Test with limit=0 (should clamp to 1)
    r = client.get(f"/api/user/projects/{project_id}/issues/abc123/events?limit=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1  # Clamped to minimum 1

    # Test with limit=300 (should clamp to 200)
    r = client.get(f"/api/user/projects/{project_id}/issues/abc123/events?limit=300")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 10  # All events, but limit was clamped to 200


def test_user_get_event_success(app_and_client_with_user):
    """Test getting event successfully (covers line 279)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create event
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        event = models.Event(
            project_id=project_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            level="error",
            message="Test error",
            fingerprint="abc123",
            payload={"test": "data"}
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/events/{event_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(event_id)
    assert data["project_id"] == project_id
    assert data["message"] == "Test error"
    assert data["payload"] == {"test": "data"}


def test_user_list_issues_not_owned(app_and_client_with_user):
    """Test listing issues fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        r = client.get(f"/api/user/projects/{other_project.id}/issues")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_list_issue_events_not_owned(app_and_client_with_user):
    """Test listing issue events fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        r = client.get(f"/api/user/projects/{other_project.id}/issues/abc123/events")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_get_event_not_owned_project(app_and_client_with_user):
    """Test getting event fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project and event
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        event = models.Event(
            project_id=other_project.id,
            timestamp=datetime.now(timezone.utc),
            level="error",
            message="Test",
            fingerprint="abc123",
            payload={}
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        r = client.get(f"/api/user/projects/{other_project.id}/events/{event.id}")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_get_event_not_found(app_and_client_with_user):
    """Test getting non-existent event"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    fake_id = uuid4()
    r = client.get(f"/api/user/projects/{project_id}/events/{fake_id}")
    assert r.status_code == 404


def test_user_get_event_wrong_project(app_and_client_with_user):
    """Test getting event from wrong project"""
    mainmod, client, user = app_and_client_with_user

    # Create two projects
    r1 = client.post("/api/user/projects", json={"name": "Project 1"})
    project_id_1 = r1.json()["id"]

    r2 = client.post("/api/user/projects", json={"name": "Project 2"})
    project_id_2 = r2.json()["id"]

    # Create event in project 1
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        event = models.Event(
            project_id=project_id_1,
            timestamp=datetime.now(timezone.utc),
            level="error",
            message="Test",
            fingerprint="abc123",
            payload={}
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        # Try to get event from project 2
        r = client.get(f"/api/user/projects/{project_id_2}/events/{event.id}")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_get_usage(app_and_client_with_user):
    """GET /api/user/usage returns current count, limit, plan, is_exceeded, is_near_limit."""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/usage")
    assert r.status_code == 200
    data = r.json()
    assert "current_count" in data
    assert "limit" in data
    assert data["plan"] in ("Free", "Basic", "Pro")
    assert "is_exceeded" in data
    assert "is_near_limit" in data
    assert data["current_count"] >= 0


def test_user_list_project_events_empty(app_and_client_with_user):
    """GET project events when none in last 30 days returns empty list."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/events")
    assert r.status_code == 200
    assert r.json() == []


def test_user_get_project_event_frequency_empty(app_and_client_with_user):
    """GET project event frequency when no events returns empty frequency and total 0."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/events/frequency")
    assert r.status_code == 200
    data = r.json()
    assert data["frequency"] == {}
    assert data["total"] == 0


def test_user_list_project_events_and_frequency_with_events(app_and_client_with_user):
    """GET project events and frequency with stored events returns data."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        evt = models.Event(
            project_id=project_id,
            timestamp=datetime.now(timezone.utc) - timedelta(days=1),
            level="error",
            message="test",
            payload={},
            fingerprint="fp1",
        )
        db.add(evt)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/events")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0].get("message") == "test"

    r = client.get(f"/api/user/projects/{project_id}/events/frequency")
    assert r.status_code == 200
    freq = r.json()
    assert freq["total"] >= 1
    assert isinstance(freq["frequency"], dict)
    assert len(freq["frequency"]) >= 1

    r = client.get(f"/api/user/projects/{project_id}/issues/fp1/events")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.get(f"/api/user/projects/{project_id}/issues/fp1/events/frequency")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert isinstance(data["frequency"], dict)


def test_user_get_issue_event_frequency_empty(app_and_client_with_user):
    """GET issue event frequency when no events for fingerprint returns empty."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/issues/fp123/events/frequency")
    assert r.status_code == 200
    data = r.json()
    assert data["frequency"] == {}
    assert data["total"] == 0


def test_user_get_alert_settings_default(app_and_client_with_user):
    """GET alert-settings when no row exists returns defaults"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is False
    assert data["level_filter"] == "error"
    assert data["cooldown_minutes"] is None
    assert data["additional_emails"] == []


def test_user_update_and_get_alert_settings(app_and_client_with_user):
    """PATCH alert-settings and GET returns updated values"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"enabled": True, "cooldown_minutes": 60, "additional_emails": ["a@x.com", "b@x.com"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert data["cooldown_minutes"] == 60
    assert set(data["additional_emails"]) == {"a@x.com", "b@x.com"}

    r2 = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r2.status_code == 200
    assert r2.json()["enabled"] is True
    assert r2.json()["additional_emails"]  # order may vary


def test_user_update_alert_settings_too_many_recipients_400(app_and_client_with_user):
    """PATCH alert-settings with more than MAX_ALERT_RECIPIENTS returns 400."""
    mainmod, client, user = app_and_client_with_user

    from xrayradar_server.constants import MAX_ALERT_RECIPIENTS

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    too_many = [f"u{i}@example.com" for i in range(MAX_ALERT_RECIPIENTS + 1)]
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"additional_emails": too_many},
    )
    assert r.status_code == 400
    assert "at most" in r.json().get("detail", "").lower() or str(MAX_ALERT_RECIPIENTS) in r.json().get("detail", "")


def test_user_update_alert_settings_cooldown_too_low_400(app_and_client_with_user):
    """PATCH alert-settings with cooldown below plan minimum returns 400."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    # Free plan min cooldown is 10; 5 is too low
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"cooldown_minutes": 5},
    )
    assert r.status_code == 400
    assert "cooldown" in r.json().get("detail", "").lower()


def test_user_update_alert_settings_normalizes_emails(app_and_client_with_user):
    """PATCH alert-settings normalizes, dedupes, and filters invalid emails."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    # Send mix: valid, duplicate (different case), empty, non-string, whitespace
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={
            "additional_emails": [
                "valid@example.com",
                "VALID@EXAMPLE.COM",  # duplicate (same after normalize)
                "",  # empty
                "  another@example.com  ",  # whitespace
                "another@example.com",  # duplicate
            ]
        },
    )
    assert r.status_code == 200
    data = r.json()
    # Should be normalized, deduped: ["valid@example.com", "another@example.com"]
    assert len(data["additional_emails"]) == 2
    assert "valid@example.com" in data["additional_emails"]
    assert "another@example.com" in data["additional_emails"]


def test_user_get_alert_settings_cooldown_clamped(app_and_client_with_user):
    """GET alert-settings when stored cooldown < min_cooldown returns clamped value."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        settings = models.ProjectAlertSettings(
            project_id=project_id,
            enabled=True,
            cooldown_minutes=5,  # below Free plan min of 10
        )
        db.add(settings)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    data = r.json()
    assert data["cooldown_minutes"] == 10  # clamped to min_cooldown_minutes
    assert data["min_cooldown_minutes"] == 10


def test_user_alert_settings_other_project_404(app_and_client_with_user):
    """GET/PATCH alert-settings for non-owned project returns 404"""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(
            email="other@example.com",
            password_hash="hash",
            plan="Free",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        proj = models.Project(name="Other", owner_user_id=other_user.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        other_id = proj.id
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{other_id}/alert-settings")
    assert r.status_code == 404

    r2 = client.patch(
        f"/api/user/projects/{other_id}/alert-settings",
        json={"enabled": True},
    )
    assert r2.status_code == 404


def test_user_update_alert_settings_level_filter(app_and_client_with_user):
    """PATCH alert-settings with level_filter updates it"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"enabled": True, "level_filter": "warning"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["level_filter"] == "warning"

    r2 = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r2.status_code == 200
    assert r2.json()["level_filter"] == "warning"


def test_user_update_alert_settings_replace_recipients(app_and_client_with_user):
    """PATCH alert-settings replaces existing recipients"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    # First set some recipients
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"additional_emails": ["old1@x.com", "old2@x.com"]},
    )
    assert r.status_code == 200
    assert set(r.json()["additional_emails"]) == {"old1@x.com", "old2@x.com"}

    # Replace with new recipients (deletes old, inserts new)
    r2 = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"additional_emails": ["new@x.com"]},
    )
    assert r2.status_code == 200
    assert r2.json()["additional_emails"] == ["new@x.com"]

    # Verify old ones are gone
    r3 = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r3.status_code == 200
    assert "old1@x.com" not in r3.json()["additional_emails"]
    assert "old2@x.com" not in r3.json()["additional_emails"]


def test_user_deletion_request_flow(app_and_client_with_user):
    """Request deletion, get request, cancel request."""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/deletion-request")
    assert r.status_code == 200
    assert r.json() is None

    r = client.post(
        "/api/user/deletion-request",
        json={"reason": "No longer needed"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == user["id"]
    assert data["reason"] == "No longer needed"
    assert "id" in data
    assert "created_at" in data

    r = client.get("/api/user/deletion-request")
    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["reason"] == "No longer needed"

    r = client.delete("/api/user/deletion-request")
    assert r.status_code == 200

    r = client.get("/api/user/deletion-request")
    assert r.status_code == 200
    assert r.json() is None


def test_user_deletion_request_duplicate_400(app_and_client_with_user):
    """Second deletion request while one is pending returns 400."""
    mainmod, client, user = app_and_client_with_user

    r = client.post("/api/user/deletion-request", json={})
    assert r.status_code == 200

    r = client.post("/api/user/deletion-request", json={})
    assert r.status_code == 400
    assert "pending" in r.json().get("detail", "").lower()


def test_user_cancel_deletion_request_no_pending_404(app_and_client_with_user):
    """Cancel deletion request when none pending returns 404."""
    mainmod, client, user = app_and_client_with_user

    # Ensure we're logged in (session from signup in fixture)
    r = client.get("/api/me")
    assert r.status_code == 200

    r = client.delete("/api/user/deletion-request")
    assert r.status_code == 404
