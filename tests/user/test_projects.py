"""Tests for user projects and usage endpoints."""

import xrayradar_server.models as models


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

    r1 = client.post("/api/user/projects", json={"name": "Project 1"})
    assert r1.status_code == 200

    r2 = client.get("/api/user/projects")
    assert r2.status_code == 200
    projects = r2.json()
    assert len(projects) == 1
    assert projects[0]["name"] == "Project 1"


def test_user_update_project_owner(app_and_client_with_user):
    """Project owner can update project name via PATCH."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "Original Name"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r2 = client.patch(f"/api/user/projects/{project_id}", json={"name": "Updated Name"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "Updated Name"
    assert r2.json()["id"] == project_id
    assert r2.json()["is_owner"] is True

    r3 = client.get("/api/user/projects")
    assert r3.status_code == 200
    proj = next((p for p in r3.json() if p["id"] == project_id), None)
    assert proj is not None
    assert proj["name"] == "Updated Name"


def test_user_update_project_non_owner_404(app_and_client_with_user):
    """Non-owner (member) cannot update project name; gets 404."""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        owner = models.User(
            email="owner@example.com",
            password_hash="hash",
            plan="Free",
            email_verified=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        proj = models.Project(name="Owner Project", owner_user_id=owner.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        db.add(models.ProjectMember(project_id=proj.id, user_id=user["id"]))
        db.commit()
        project_id = proj.id
    finally:
        db.close()

    r = client.patch(f"/api/user/projects/{project_id}", json={"name": "Hacked Name"})
    assert r.status_code == 404
    # Name unchanged
    db2 = dbmod.SessionLocal()
    try:
        p = db2.get(models.Project, project_id)
        assert p.name == "Owner Project"
    finally:
        db2.close()


def test_user_get_usage(app_and_client_with_user):
    """GET /api/user/usage returns current count, limit, plan."""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/usage")
    assert r.status_code == 200
    data = r.json()
    assert "current_count" in data
    assert "limit" in data
    assert data["plan"] in ("Free", "Basic", "Teams", "Teams Pro")
    assert "is_exceeded" in data
    assert "is_near_limit" in data
    assert data["current_count"] >= 0
