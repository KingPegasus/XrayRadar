"""Tests for user alert-settings endpoints."""

import xrayradar_server.db as dbmod
from xrayradar_server import models


def _set_plan(db, user_id, plan):
    u = db.get(models.User, user_id)
    if u:
        u.plan = plan
        db.add(u)
        db.commit()


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


def test_user_free_plan_cannot_enable_alerts_400(app_and_client_with_user):
    """PATCH alert-settings with enabled=True as Free user returns 400."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"enabled": True},
    )
    assert r.status_code == 400
    assert "Free" in r.json().get("detail", "")
    assert "alerts" in r.json().get("detail", "").lower()


def test_user_update_and_get_alert_settings(app_and_client_with_user):
    """PATCH alert-settings and GET returns updated values"""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()

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
    assert r2.json()["additional_emails"]


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
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")  # Basic min = 10 min
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"cooldown_minutes": 5},
    )
    assert r.status_code == 400
    assert "cooldown" in r.json().get("detail", "").lower()


def test_user_update_alert_settings_normalizes_emails(app_and_client_with_user):
    """PATCH alert-settings normalizes, dedupes, and filters invalid emails."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={
            "additional_emails": [
                "valid@example.com",
                "VALID@EXAMPLE.COM",
                "",
                "  another@example.com  ",
                "another@example.com",
            ]
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["additional_emails"]) == 2
    assert "valid@example.com" in data["additional_emails"]
    assert "another@example.com" in data["additional_emails"]


def test_user_get_alert_settings_cooldown_clamped(app_and_client_with_user):
    """GET alert-settings when stored cooldown < min_cooldown returns clamped value."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    db2 = dbmod.SessionLocal()
    try:
        settings = models.ProjectAlertSettings(
            project_id=project_id,
            enabled=True,
            cooldown_minutes=5,
        )
        db2.add(settings)
        db2.commit()
    finally:
        db2.close()

    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    data = r.json()
    assert data["cooldown_minutes"] == 10
    assert data["min_cooldown_minutes"] == 10


def test_user_alert_settings_other_project_404(app_and_client_with_user):
    """GET/PATCH alert-settings for non-owned project returns 404"""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
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

    r2 = client.patch(f"/api/user/projects/{other_id}/alert-settings", json={"enabled": True})
    assert r2.status_code == 404


def test_member_cannot_get_or_patch_alert_settings(app_and_client_with_user):
    """Project members (non-owners) cannot access alert settings endpoints."""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        owner = models.User(email="owner-alerts@example.com", password_hash="hash", plan="Teams")
        db.add(owner)
        db.commit()
        db.refresh(owner)
        proj = models.Project(name="Owner Project", owner_user_id=owner.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        db.add(models.ProjectMember(project_id=proj.id, user_id=user["id"]))
        db.commit()
        shared_project_id = proj.id
    finally:
        db.close()

    r_get = client.get(f"/api/user/projects/{shared_project_id}/alert-settings")
    assert r_get.status_code == 404

    r_patch = client.patch(
        f"/api/user/projects/{shared_project_id}/alert-settings",
        json={"enabled": True},
    )
    assert r_patch.status_code == 404


def test_user_update_alert_settings_level_filter(app_and_client_with_user):
    """PATCH alert-settings with level_filter updates it"""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()

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
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"additional_emails": ["old1@x.com", "old2@x.com"]},
    )
    assert r.status_code == 200
    assert set(r.json()["additional_emails"]) == {"old1@x.com", "old2@x.com"}

    r2 = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"additional_emails": ["new@x.com"]},
    )
    assert r2.status_code == 200
    assert r2.json()["additional_emails"] == ["new@x.com"]

    r3 = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r3.status_code == 200
    assert "old1@x.com" not in r3.json()["additional_emails"]
    assert "old2@x.com" not in r3.json()["additional_emails"]


def test_user_get_alert_settings_free_plan_returns_disabled_and_no_min_cooldown(app_and_client_with_user):
    """GET alert-settings as Free plan returns enabled=False, min_cooldown_minutes=None, environment_settings=[]."""
    mainmod, client, user = app_and_client_with_user
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is False
    assert data["min_cooldown_minutes"] is None
    assert data["environment_settings"] == []


def test_user_get_alert_settings_with_environment_settings(app_and_client_with_user):
    """GET alert-settings returns environment_settings when present."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    db2 = dbmod.SessionLocal()
    try:
        db2.add(
            models.ProjectAlertSettings(
                project_id=project_id,
                enabled=True,
                level_filter="error",
                cooldown_minutes=15,
            )
        )
        db2.add(
            models.ProjectAlertEnvironmentSetting(
                project_id=project_id,
                environment="production",
                enabled=True,
                cooldown_minutes=5,
            )
        )
        db2.add(
            models.ProjectAlertEnvironmentRecipient(
                project_id=project_id,
                environment="production",
                email="prod@example.com",
            )
        )
        db2.commit()
    finally:
        db2.close()
    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    data = r.json()
    assert len(data["environment_settings"]) == 1
    assert data["environment_settings"][0]["environment"] == "production"
    assert data["environment_settings"][0]["enabled"] is True
    assert data["environment_settings"][0]["cooldown_minutes"] == 5
    assert "prod@example.com" in data["environment_settings"][0]["additional_emails"]


def test_user_update_alert_settings_environment_settings(app_and_client_with_user):
    """PATCH alert-settings with environment_settings creates env settings and recipients."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={
            "enabled": True,
            "environment_settings": [
                {
                    "environment": "staging",
                    "enabled": True,
                    "cooldown_minutes": 20,
                    "additional_emails": ["staging@example.com"],
                },
            ],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["environment_settings"]) == 1
    assert data["environment_settings"][0]["environment"] == "staging"
    assert data["environment_settings"][0]["cooldown_minutes"] == 20
    assert data["environment_settings"][0]["additional_emails"] == ["staging@example.com"]
    r2 = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r2.status_code == 200
    assert r2.json()["environment_settings"][0]["environment"] == "staging"


def test_user_get_alert_settings_hides_environment_settings_for_basic(app_and_client_with_user):
    """Basic plan should not see environment settings even if legacy rows exist."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    db2 = dbmod.SessionLocal()
    try:
        db2.add(
            models.ProjectAlertEnvironmentSetting(
                project_id=project_id,
                environment="production",
                enabled=True,
                cooldown_minutes=5,
            )
        )
        db2.add(
            models.ProjectAlertEnvironmentRecipient(
                project_id=project_id,
                environment="production",
                email="prod@example.com",
            )
        )
        db2.commit()
    finally:
        db2.close()
    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    assert r.json()["environment_settings"] == []


def test_user_update_alert_settings_environment_settings_rejected_for_basic(app_and_client_with_user):
    """Basic plan cannot set environment-based alert settings."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={
            "environment_settings": [
                {"environment": "development", "enabled": True, "cooldown_minutes": 20}
            ]
        },
    )
    assert r.status_code == 400
    assert "teams" in r.json().get("detail", "").lower()


def test_user_get_alert_settings_teams_pro_returns_min_cooldown_1(app_and_client_with_user):
    """GET alert-settings as Teams Pro returns min_cooldown_minutes=1 (same as Teams)."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams Pro")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    r = client.get(f"/api/user/projects/{project_id}/alert-settings")
    assert r.status_code == 200
    data = r.json()
    assert data["min_cooldown_minutes"] == 1


def test_user_update_alert_settings_teams_pro_environment_settings(app_and_client_with_user):
    """Teams Pro plan can set environment-based alert settings (same as Teams)."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Teams Pro")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={
            "enabled": True,
            "environment_settings": [
                {
                    "environment": "production",
                    "enabled": True,
                    "cooldown_minutes": 1,
                    "additional_emails": ["prod@example.com"],
                },
            ],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["environment_settings"]) == 1
    assert data["environment_settings"][0]["environment"] == "production"
    assert data["environment_settings"][0]["cooldown_minutes"] == 1
    assert "prod@example.com" in data["environment_settings"][0]["additional_emails"]


def test_user_basic_plan_can_save_additional_emails_without_environment_settings(app_and_client_with_user):
    """Basic plan can save project-level additional_emails; no environment_settings sent."""
    mainmod, client, user = app_and_client_with_user
    db = dbmod.SessionLocal()
    try:
        _set_plan(db, user["id"], "Basic")
    finally:
        db.close()
    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]
    r = client.patch(
        f"/api/user/projects/{project_id}/alert-settings",
        json={"enabled": True, "cooldown_minutes": 15, "additional_emails": ["alerts@example.com"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert data["additional_emails"] == ["alerts@example.com"]
    assert data["environment_settings"] == []
