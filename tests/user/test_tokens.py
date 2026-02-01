"""Tests for user tokens and token-requests endpoints."""

from datetime import datetime, timezone

from xrayradar_server import models


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

    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        access = models.TokenProjectAccess(token_id=token.id, project_id=project_id)
        db.add(access)
        db.commit()

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

        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        r = client.post(f"/api/user/tokens/{token.id}/projects/{other_project.id}/grant")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_grant_project_access_not_user_token(app_and_client_with_user):
    """Test granting access fails for non-user token"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    r = client.post(f"/api/user/tokens/1/projects/{project_id}/grant")
    assert r.status_code == 404


def test_user_grant_project_access_revoked_token(app_and_client_with_user):
    """Test granting access fails for revoked token"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

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

    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        r = client.post(f"/api/user/tokens/{token.id}/projects/{project_id}/grant")
        assert r.status_code == 200
        assert r.json()["ok"] is True
    finally:
        db.close()


def test_user_grant_project_access_revoked_access(app_and_client_with_user):
    """Test granting access when access exists but is revoked"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token="test-token", user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)

        access = models.TokenProjectAccess(
            token_id=token.id,
            project_id=project_id,
            revoked_at=datetime.now(timezone.utc)
        )
        db.add(access)
        db.commit()

        r = client.post(f"/api/user/tokens/{token.id}/projects/{project_id}/grant")
        assert r.status_code == 200
        assert r.json()["ok"] is True

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
