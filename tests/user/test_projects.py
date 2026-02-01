"""Tests for user projects and usage endpoints."""


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


def test_user_get_usage(app_and_client_with_user):
    """GET /api/user/usage returns current count, limit, plan."""
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
