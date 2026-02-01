"""Tests for user alert-settings endpoints."""

from xrayradar_server import models


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

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        settings = models.ProjectAlertSettings(
            project_id=project_id,
            enabled=True,
            cooldown_minutes=5,
        )
        db.add(settings)
        db.commit()
    finally:
        db.close()

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
