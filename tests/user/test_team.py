"""Tests for Pro team endpoints: members, invites, assign, revoke."""

import pytest
from sqlalchemy import select

import xrayradar_server.models as models


def _set_plan(db, user_id, plan):
    u = db.get(models.User, user_id)
    if u:
        u.plan = plan
        db.add(u)
        db.commit()


def test_team_list_members_requires_pro(app_and_client_with_user):
    """GET /api/user/team/members returns 403 when user is not Pro."""
    mainmod, client, user = app_and_client_with_user
    r = client.get("/api/user/team/members")
    assert r.status_code == 403
    assert "Teams" in (r.json().get("detail") or "")


def test_team_list_members_empty(app_and_client_with_user):
    """GET /api/user/team/members returns [] for Pro user with no members."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r = client.get("/api/user/team/members")
    assert r.status_code == 200
    assert r.json() == []


def test_team_invites_requires_pro(app_and_client_with_user):
    """GET /api/user/team/invites returns 403 when user is not Pro."""
    mainmod, client, user = app_and_client_with_user
    r = client.get("/api/user/team/invites")
    assert r.status_code == 403


def test_project_add_member_requires_pro(app_and_client_with_user):
    """POST /api/user/projects/:id/members returns 403 when user is not Pro."""
    mainmod, client, user = app_and_client_with_user
    r1 = client.post("/api/user/projects", json={"name": "P1"})
    assert r1.status_code == 200
    pid = r1.json()["id"]
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "other@example.com"},
    )
    assert r.status_code == 403


def test_project_add_member_pro_success(app_and_client_with_user):
    """Pro user can add another user to their project by email."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        # Create second user (member)
        other = models.User(
            email="member@example.com",
            password_hash="hash",
            plan="Free",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        other_id = other.id
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "Proj"})
    assert r1.status_code == 200
    pid = r1.json()["id"]

    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "member@example.com"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "member@example.com"
    assert data["user_id"] == other_id
    assert pid in data["project_ids"]

    # List members includes them
    r2 = client.get("/api/user/team/members")
    assert r2.status_code == 200
    members = r2.json()
    assert len(members) == 1
    assert members[0]["email"] == "member@example.com"
    assert members[0]["project_ids"] == [pid]


def test_project_revoke_member(app_and_client_with_user):
    """Pro user can revoke a member's project access."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="revoke@example.com",
            password_hash="hash",
            plan="Free",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        other_id = other.id
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    pid = r1.json()["id"]
    client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "revoke@example.com"},
    )
    r = client.delete(f"/api/user/projects/{pid}/members/{other_id}")
    assert r.status_code == 204
    r2 = client.get("/api/user/team/members")
    assert r2.status_code == 200
    assert len(r2.json()) == 0


def test_team_remove_member(app_and_client_with_user):
    """Pro user can remove a member from all their projects."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="remove@example.com",
            password_hash="hash",
            plan="Free",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        other_id = other.id
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    pid = r1.json()["id"]
    client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "remove@example.com"},
    )
    r = client.delete(f"/api/user/team/members/{other_id}")
    assert r.status_code == 204
    r2 = client.get("/api/user/team/members")
    assert r2.status_code == 200
    assert len(r2.json()) == 0


def test_team_create_invite_pro(app_and_client_with_user):
    """Pro user can create a team invite."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    pid = r1.json()["id"]

    r = client.post(
        "/api/user/team/invites",
        json={"email": "invited@example.com", "project_ids": [pid]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "invited@example.com"
    assert data["project_ids"] == [pid]
    assert "id" in data
    assert "expires_at" in data


def test_require_project_access_member_can_access(app_and_client_with_user):
    """A project member can access the project (issues list)."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        owner = models.User(
            email="owner@example.com",
            password_hash="hash",
            plan="Teams",
            email_verified=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        proj = models.Project(name="Shared", owner_user_id=owner.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        db.add(models.ProjectMember(project_id=proj.id, user_id=user["id"]))
        db.commit()
        pid = proj.id
    finally:
        db.close()

    # Current user (member, not owner) can list issues for the project
    r = client.get(f"/api/user/projects/{pid}/issues")
    assert r.status_code == 200


def test_user_list_projects_includes_is_owner(app_and_client_with_user):
    """GET /api/user/projects returns is_owner for each project."""
    mainmod, client, user = app_and_client_with_user
    r1 = client.post("/api/user/projects", json={"name": "Mine"})
    assert r1.status_code == 200
    r2 = client.get("/api/user/projects")
    assert r2.status_code == 200
    projects = r2.json()
    assert len(projects) >= 1
    mine = next((p for p in projects if p["name"] == "Mine"), None)
    assert mine is not None
    assert mine.get("is_owner") is True


def test_team_accept_invite_requires_auth(app_and_client_with_user):
    """POST /api/user/team/invites/accept without session returns 401."""
    mainmod, client, user = app_and_client_with_user
    # Use a new client without session
    from fastapi.testclient import TestClient
    guest = TestClient(mainmod.app)
    r = guest.post(
        "/api/user/team/invites/accept",
        json={"token": "sometoken"},
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 401


def test_team_accept_invite_success(app_and_client_with_user):
    """Invited user can accept invite and gets project access."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    from datetime import datetime, timezone, timedelta
    db = dbmod.SessionLocal()
    invite_token = None
    try:
        _set_plan(db, user["id"], "Teams")
        r1 = client.post("/api/user/projects", json={"name": "Shared"})
        assert r1.status_code == 200
        pid = r1.json()["id"]
        r2 = client.post(
            "/api/user/team/invites",
            json={"email": "invited@example.com", "project_ids": [pid]},
        )
        assert r2.status_code == 200
        inv_id = r2.json()["id"]
        inv = db.get(models.TeamInvite, inv_id)
        assert inv is not None
        invite_token = inv.token
        # Create invited user with known password (they will login and accept)
        from xrayradar_server.auth import hash_password
        other = models.User(
            email="invited@example.com",
            password_hash=hash_password("password123"),
            plan="Free",
            email_verified=True,
        )
        db.add(other)
        db.commit()
    finally:
        db.close()

    # Login as invited user (overwrites session)
    r3 = client.post(
        "/auth/login",
        json={"email": "invited@example.com", "password": "password123"},
    )
    assert r3.status_code == 200

    r4 = client.post(
        "/api/user/team/invites/accept",
        json={"token": invite_token},
    )
    assert r4.status_code == 204

    # Invited user now sees the project
    r5 = client.get("/api/user/projects")
    assert r5.status_code == 200
    projects = r5.json()
    assert any(p["id"] == pid for p in projects)
