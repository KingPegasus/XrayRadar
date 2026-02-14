"""Tests for Pro team endpoints: members, invites, assign, revoke."""

from unittest.mock import patch

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


def test_project_member_list_environments_requires_pro(app_and_client_with_user):
    """GET member environments returns 403 when user is not Pro."""
    mainmod, client, user = app_and_client_with_user
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    pid = r1.json()["id"]
    r = client.get(f"/api/user/projects/{pid}/members/999/environments")
    assert r.status_code == 403


def test_project_member_list_environments_empty_and_after_replace(app_and_client_with_user):
    """GET member environments returns [] initially; PUT replaces; GET returns new list."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="envmember@example.com",
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

    r1 = client.post("/api/user/projects", json={"name": "EnvProj"})
    assert r1.status_code == 200
    pid = r1.json()["id"]
    client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "envmember@example.com"},
    )

    r = client.get(f"/api/user/projects/{pid}/members/{other_id}/environments")
    assert r.status_code == 200
    assert r.json() == []

    r_put = client.put(
        f"/api/user/projects/{pid}/members/{other_id}/environments",
        json={"environments": ["production", "staging"]},
    )
    assert r_put.status_code == 200
    assert r_put.json() == {"ok": True, "environments": ["production", "staging"]}

    r2 = client.get(f"/api/user/projects/{pid}/members/{other_id}/environments")
    assert r2.status_code == 200
    assert set(r2.json()) == {"production", "staging"}

    client.put(
        f"/api/user/projects/{pid}/members/{other_id}/environments",
        json={"environments": []},
    )
    r3 = client.get(f"/api/user/projects/{pid}/members/{other_id}/environments")
    assert r3.status_code == 200
    assert r3.json() == []


def test_project_member_replace_environments_member_not_found(app_and_client_with_user):
    """PUT member environments returns 404 when member is not on the project."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="stranger@example.com",
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
    r = client.put(
        f"/api/user/projects/{pid}/members/{other_id}/environments",
        json={"environments": ["production"]},
    )
    assert r.status_code == 404


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


def test_project_add_member_both_user_id_and_email(app_and_client_with_user):
    """POST add member with both user_id and email returns 400."""
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
        f"/api/user/projects/{pid}/members",
        json={"user_id": 1, "email": "a@b.com"},
    )
    assert r.status_code == 400
    assert "not both" in (r.json().get("detail") or "")


def test_project_add_member_neither_user_id_nor_email(app_and_client_with_user):
    """POST add member without user_id or email returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    r = client.post(f"/api/user/projects/{pid}/members", json={})
    assert r.status_code == 400


def test_project_add_member_user_not_found_by_id(app_and_client_with_user):
    """POST add member with non-existent user_id returns 404."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"user_id": 99999},
    )
    assert r.status_code == 404


def test_project_add_member_user_not_found_by_email(app_and_client_with_user):
    """POST add member with unknown email returns 404."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "nobody@example.com"},
    )
    assert r.status_code == 404


def test_project_add_member_cannot_add_self(app_and_client_with_user):
    """POST add member with own user_id or email returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"user_id": user["id"]},
    )
    assert r.status_code == 400
    assert "yourself" in (r.json().get("detail") or "").lower()


def test_project_add_member_already_member(app_and_client_with_user):
    """POST add member when user already has access returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="already@example.com",
            password_hash="h",
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
    pid = r1.json()["id"]
    client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "already@example.com"},
    )
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"user_id": other_id},
    )
    assert r.status_code == 400
    assert "already" in (r.json().get("detail") or "").lower()


def test_project_add_member_by_user_id_success(app_and_client_with_user):
    """Pro user can add member by user_id."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="byid@example.com",
            password_hash="h",
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
    pid = r1.json()["id"]
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"user_id": other_id},
    )
    assert r.status_code == 200
    assert r.json()["user_id"] == other_id
    assert r.json()["email"] == "byid@example.com"


def test_project_add_member_project_not_owned(app_and_client_with_user):
    """POST add member to project owned by another returns 404."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other_owner = models.User(
            email="owner@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(other_owner)
        db.commit()
        db.refresh(other_owner)
        proj = models.Project(name="Other", owner_user_id=other_owner.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        other_pid = proj.id
    finally:
        db.close()
    other_member = models.User(
        email="member@example.com",
        password_hash="h",
        plan="Free",
        email_verified=True,
    )
    db2 = dbmod.SessionLocal()
    try:
        db2.add(other_member)
        db2.commit()
        db2.refresh(other_member)
        mid = other_member.id
    finally:
        db2.close()
    r = client.post(
        f"/api/user/projects/{other_pid}/members",
        json={"user_id": mid},
    )
    assert r.status_code == 404


def test_project_revoke_member_project_not_owned(app_and_client_with_user):
    """DELETE revoke member on project not owned returns 404."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="revokeowner@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        proj = models.Project(name="Other", owner_user_id=other.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
    finally:
        db.close()
    r = client.delete(f"/api/user/projects/{proj.id}/members/1")
    assert r.status_code == 404


def test_team_create_invite_empty_project_ids(app_and_client_with_user):
    """POST team invites with empty project_ids returns 400 or 422 (validation)."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r = client.post(
        "/api/user/team/invites",
        json={"email": "inv@example.com", "project_ids": []},
    )
    assert r.status_code in (400, 422)


def test_team_create_invite_project_not_owned(app_and_client_with_user):
    """POST team invites with project not owned returns 404."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        other = models.User(
            email="invowner@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        proj = models.Project(name="Other", owner_user_id=other.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        other_pid = proj.id
    finally:
        db.close()
    r = client.post(
        "/api/user/team/invites",
        json={"email": "inv@example.com", "project_ids": [other_pid]},
    )
    assert r.status_code == 404


def test_team_create_invite_empty_email(app_and_client_with_user):
    """POST team invites with empty email returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    r = client.post(
        "/api/user/team/invites",
        json={"email": "  ", "project_ids": [pid]},
    )
    assert r.status_code == 400


def test_team_list_invites_after_create(app_and_client_with_user):
    """GET team invites returns created invites."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    client.post(
        "/api/user/team/invites",
        json={"email": "listinv@example.com", "project_ids": [pid]},
    )
    r = client.get("/api/user/team/invites")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert any(inv["email"] == "listinv@example.com" for inv in data)


def test_team_accept_invite_token_required(app_and_client_with_user):
    """POST accept invite with empty token returns 400."""
    mainmod, client, user = app_and_client_with_user
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": "   "},
    )
    assert r.status_code == 400


def test_team_accept_invite_not_found(app_and_client_with_user):
    """POST accept invite with unknown token returns 404."""
    mainmod, client, user = app_and_client_with_user
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": "nonexistent-token-123"},
    )
    assert r.status_code == 404


def test_team_accept_invite_already_used(app_and_client_with_user):
    """POST accept invite when invite already used returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        r1 = client.post("/api/user/projects", json={"name": "P"})
        pid = r1.json()["id"]
        r2 = client.post(
            "/api/user/team/invites",
            json={"email": "used@example.com", "project_ids": [pid]},
        )
        inv_id = r2.json()["id"]
        inv = db.get(models.TeamInvite, inv_id)
        from datetime import datetime, timezone
        inv.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(inv)
        db.commit()
        used_token = inv.token
    finally:
        db.close()
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": used_token},
    )
    assert r.status_code == 400
    assert "already used" in (r.json().get("detail") or "").lower()


def test_team_accept_invite_expired(app_and_client_with_user):
    """POST accept invite when invite expired returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    from datetime import datetime, timezone, timedelta
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        r1 = client.post("/api/user/projects", json={"name": "P"})
        pid = r1.json()["id"]
        r2 = client.post(
            "/api/user/team/invites",
            json={"email": "expired@example.com", "project_ids": [pid]},
        )
        inv_id = r2.json()["id"]
        inv = db.get(models.TeamInvite, inv_id)
        inv.expires_at = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1))
        db.add(inv)
        db.commit()
        expired_token = inv.token
    finally:
        db.close()
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": expired_token},
    )
    assert r.status_code == 400
    assert "expired" in (r.json().get("detail") or "").lower()


def test_team_accept_invite_email_mismatch(app_and_client_with_user):
    """POST accept invite when logged-in user email does not match invite returns 403."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        r1 = client.post("/api/user/projects", json={"name": "P"})
        pid = r1.json()["id"]
        r2 = client.post(
            "/api/user/team/invites",
            json={"email": "different@example.com", "project_ids": [pid]},
        )
        inv_id = r2.json()["id"]
        inv = db.get(models.TeamInvite, inv_id)
        token = inv.token
    finally:
        db.close()
    # Current user is the inviter (e.g. test user); invite was for different@example.com.
    # So accepting with current session (inviter's email) should get 403.
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": token},
    )
    assert r.status_code == 403
    assert "different" in (r.json().get("detail") or "").lower() or "email" in (r.json().get("detail") or "").lower()


def test_team_member_limit_on_add_member(app_and_client_with_user):
    """Adding members when at plan limit returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    # Teams plan allows 5 members; add 5 then try to add 6th (must exist to hit limit, not 404)
    try:
        _set_plan(db, user["id"], "Teams")
        for i in range(6):
            other = models.User(
                email=f"limit{i}@example.com",
                password_hash="h",
                plan="Free",
                email_verified=True,
            )
            db.add(other)
        db.commit()
        users = list(db.execute(select(models.User).where(models.User.email.like("limit%@example.com"))).scalars().all())
        user_ids = [u.id for u in users]
        assert len(user_ids) >= 5
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    for uid in user_ids[:5]:
        r = client.post(
            f"/api/user/projects/{pid}/members",
            json={"user_id": uid},
        )
        assert r.status_code == 200, r.json()
    r = client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "limit5@example.com"},
    )
    assert r.status_code == 400
    assert "limit" in (r.json().get("detail") or "").lower()


def test_team_member_limit_on_invite(app_and_client_with_user):
    """Creating invite when at plan limit returns 400."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
        for i in range(5):
            other = models.User(
                email=f"invlimit{i}@example.com",
                password_hash="h",
                plan="Free",
                email_verified=True,
            )
            db.add(other)
        db.commit()
        users = list(db.execute(select(models.User).where(models.User.email.like("invlimit%@example.com"))).scalars().all())
        user_ids = [u.id for u in users]
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    for uid in user_ids:
        client.post(f"/api/user/projects/{pid}/members", json={"user_id": uid})
    r = client.post(
        "/api/user/team/invites",
        json={"email": "extra@example.com", "project_ids": [pid]},
    )
    assert r.status_code == 400
    assert "limit" in (r.json().get("detail") or "").lower()


def test_get_team_member_count_with_members_and_pending(app_and_client_with_user):
    """_get_team_member_count runs member_emails loop when owner has both members and pending invites."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    # Add one member so member_ids is non-empty
    other = models.User(
        email="countmember@example.com",
        password_hash="h",
        plan="Free",
        email_verified=True,
    )
    db2 = dbmod.SessionLocal()
    try:
        db2.add(other)
        db2.commit()
        db2.refresh(other)
    finally:
        db2.close()
    client.post(
        f"/api/user/projects/{pid}/members",
        json={"email": "countmember@example.com"},
    )
    # Create one invite (different email) so pending_emails is non-empty
    client.post(
        "/api/user/team/invites",
        json={"email": "countpending@example.com", "project_ids": [pid]},
    )
    # Creating another invite calls _get_team_member_count with both members and pending
    r = client.post(
        "/api/user/team/invites",
        json={"email": "third@example.com", "project_ids": [pid]},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "third@example.com"


def test_team_create_invite_project_not_found(app_and_client_with_user):
    """POST team invites with non-existent project_id returns 404."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r = client.post(
        "/api/user/team/invites",
        json={"email": "inv@example.com", "project_ids": [99999]},
    )
    assert r.status_code == 404


def test_send_invite_email_success(app_and_client_with_user):
    """When Resend is configured and send succeeds, invite is created (covers _send_invite_email return True)."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    with patch("xrayradar_server.routers.user.team.RESEND_API_KEY", "test-key"), \
         patch("xrayradar_server.routers.user.team.RESEND_FROM_EMAIL", "from@test.com"), \
         patch("xrayradar_server.routers.user.team.XRAYRADAR_BASE_URL", "https://app.test"), \
         patch("resend.Emails.send") as mock_send:
        mock_send.return_value = None
        r = client.post(
            "/api/user/team/invites",
            json={"email": "sent@example.com", "project_ids": [pid]},
        )
    assert r.status_code == 200
    assert r.json()["email"] == "sent@example.com"
    mock_send.assert_called_once()
    call_params = mock_send.call_args[1]["params"]
    assert "sent@example.com" in call_params["to"]
    assert "accept-invite" in call_params["html"]


def test_send_invite_email_exception(app_and_client_with_user):
    """When Resend send raises, invite is still created (covers _send_invite_email except return False)."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    pid = r1.json()["id"]
    with patch("xrayradar_server.routers.user.team.RESEND_API_KEY", "test-key"), \
         patch("xrayradar_server.routers.user.team.RESEND_FROM_EMAIL", "from@test.com"), \
         patch("resend.Emails.send", side_effect=Exception("send failed")):
        r = client.post(
            "/api/user/team/invites",
            json={"email": "fail@example.com", "project_ids": [pid]},
        )
    assert r.status_code == 200
    assert r.json()["email"] == "fail@example.com"


def test_team_accept_invite_skips_nonexistent_project_id(app_and_client_with_user):
    """Accept invite skips non-existent project ids in invite list (covers continue when proj is None)."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    from xrayradar_server.auth import hash_password
    db = dbmod.SessionLocal()
    invite_token = None
    pid = None
    try:
        _set_plan(db, user["id"], "Teams")
        r1 = client.post("/api/user/projects", json={"name": "Shared"})
        assert r1.status_code == 200
        pid = r1.json()["id"]
        r2 = client.post(
            "/api/user/team/invites",
            json={"email": "skipnone@example.com", "project_ids": [pid]},
        )
        assert r2.status_code == 200
        inv_id = r2.json()["id"]
        inv = db.get(models.TeamInvite, inv_id)
        invite_token = inv.token
        # Manually add a non-existent project id to the invite so accept hits proj is None
        inv.project_ids = (inv.project_ids or []) + [99999]
        db.add(inv)
        db.commit()
        other = models.User(
            email="skipnone@example.com",
            password_hash=hash_password("password123"),
            plan="Free",
            email_verified=True,
        )
        db.add(other)
        db.commit()
    finally:
        db.close()

    client.post(
        "/auth/login",
        json={"email": "skipnone@example.com", "password": "password123"},
    )
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": invite_token},
    )
    assert r.status_code == 204
    r2 = client.get("/api/user/projects")
    projects = r2.json()
    assert any(p["id"] == pid for p in projects)


def test_team_accept_invite_skips_project_owned_by_other(app_and_client_with_user):
    """Accept invite skips project ids owned by someone else (covers continue when owner != inviter)."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    from xrayradar_server.auth import hash_password
    db = dbmod.SessionLocal()
    invite_token = None
    pid = None
    try:
        _set_plan(db, user["id"], "Teams")
        r1 = client.post("/api/user/projects", json={"name": "Mine"})
        assert r1.status_code == 200
        pid = r1.json()["id"]
        other_owner = models.User(
            email="otherowner@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(other_owner)
        db.commit()
        db.refresh(other_owner)
        other_proj = models.Project(name="Theirs", owner_user_id=other_owner.id)
        db.add(other_proj)
        db.commit()
        db.refresh(other_proj)
        other_pid = other_proj.id
        r2 = client.post(
            "/api/user/team/invites",
            json={"email": "skipother@example.com", "project_ids": [pid]},
        )
        assert r2.status_code == 200
        inv_id = r2.json()["id"]
        inv = db.get(models.TeamInvite, inv_id)
        invite_token = inv.token
        inv.project_ids = (inv.project_ids or []) + [other_pid]
        db.add(inv)
        db.commit()
        other_user = models.User(
            email="skipother@example.com",
            password_hash=hash_password("password123"),
            plan="Free",
            email_verified=True,
        )
        db.add(other_user)
        db.commit()
    finally:
        db.close()

    client.post(
        "/auth/login",
        json={"email": "skipother@example.com", "password": "password123"},
    )
    r = client.post(
        "/api/user/team/invites/accept",
        json={"token": invite_token},
    )
    assert r.status_code == 204
    r2 = client.get("/api/user/projects")
    projects = r2.json()
    assert any(p["id"] == pid for p in projects)
    assert not any(p["id"] == other_pid for p in projects)
