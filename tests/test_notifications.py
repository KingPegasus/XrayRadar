"""Tests for notifications module (email alerts and digest helpers)."""

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from xrayradar_server import models
from xrayradar_server.notifications import (
    get_project_alert_settings,
    get_alert_recipients,
    get_last_alert_sent_at,
    get_top_issues_since,
    should_send_alert,
)


@pytest.fixture
def db_session(database_url, monkeypatch):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    import xrayradar_server.db as dbmod
    # Force engine reinit without reloading db (so Base.metadata still matches models)
    if getattr(dbmod, "_engine", None) is not None:
        dbmod._engine.dispose()
    dbmod._engine = None
    dbmod._SessionLocal = None
    dbmod._engine_url = None
    dbmod.init_db()
    db = dbmod.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def project_with_owner(db_session):
    """Create a user and project owned by that user. Uses Basic plan so get_alert_recipients returns owner."""
    email = f"owner-{uuid.uuid4().hex}@example.com"
    user = models.User(
        email=email,
        password_hash="hash",
        plan="Basic",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    project = models.Project(name="Test Project", owner_user_id=user.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project, user


@pytest.fixture
def project_no_owner(db_session):
    """Create a project with no owner."""
    project = models.Project(name="Orphan", owner_user_id=None)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_get_project_alert_settings_no_row(db_session, project_with_owner):
    """When no ProjectAlertSettings row exists, return defaults."""
    project, _ = project_with_owner
    enabled, level_filter, cooldown = get_project_alert_settings(db_session, project.id)
    assert enabled is False
    assert level_filter == "error"
    assert cooldown is None


def test_get_project_alert_settings_with_row(db_session, project_with_owner):
    """When row exists, return stored values."""
    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=30,
        )
    )
    db_session.commit()
    enabled, level_filter, cooldown = get_project_alert_settings(db_session, project.id)
    assert enabled is True
    assert level_filter == "error"
    assert cooldown == 30


def test_get_project_alert_settings_ignores_environment_override_for_basic(db_session, project_with_owner):
    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=30,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="production",
            enabled=False,
            cooldown_minutes=1,
        )
    )
    db_session.commit()
    enabled, level_filter, cooldown = get_project_alert_settings(
        db_session, project.id, environment="production"
    )
    assert enabled is True
    assert level_filter == "error"
    assert cooldown == 30


def test_get_alert_recipients_owner_only(db_session, project_with_owner):
    """Recipients include owner email when no additional recipients."""
    project, user = project_with_owner
    # Ensure owner is loaded
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project)
    assert set(recipients) == {user.email}


def test_get_alert_recipients_free_plan_returns_empty(db_session, project_with_owner):
    """Free plan project owner gets no alert emails (recipients list empty)."""
    project, user = project_with_owner
    user.plan = "Free"
    db_session.add(user)
    db_session.commit()
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project)
    assert recipients == []


def test_get_alert_recipients_no_owner(db_session, project_no_owner):
    """Recipients empty when project has no owner and no additional emails."""
    project = db_session.get(models.Project, project_no_owner.id)
    recipients = get_alert_recipients(db_session, project)
    assert recipients == []


def test_get_alert_recipients_owner_missing(db_session):
    """When project has owner_user_id but user no longer exists, only additional emails returned."""
    # Use a non-existent user id so owner lookup returns None (simulates deleted/missing owner)
    project = models.Project(name="P", owner_user_id=999999)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    db_session.add(models.ProjectAlertRecipient(project_id=project.id, email="extra@x.com"))
    db_session.commit()
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project)
    assert set(recipients) == {"extra@x.com"}


def test_get_alert_recipients_owner_plus_additional(db_session, project_with_owner):
    """Recipients include owner and additional, deduped."""
    project, user = project_with_owner
    db_session.add(
        models.ProjectAlertRecipient(project_id=project.id, email="extra@x.com")
    )
    db_session.add(
        models.ProjectAlertRecipient(project_id=project.id, email=user.email)
    )
    db_session.commit()
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project)
    assert set(recipients) == {user.email, "extra@x.com"}


def test_get_alert_recipients_ignores_environment_recipients_for_basic(db_session, project_with_owner):
    project, user = project_with_owner
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="development",
            email="dev-team@example.com",
        )
    )
    db_session.commit()
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project, environment="development")
    assert set(recipients) == {user.email}


def test_get_alert_recipients_includes_environment_recipients_for_teams(db_session, project_with_owner):
    """When owner is Teams and environment is passed, env-specific recipients are included."""
    project, user = project_with_owner
    user.plan = "Teams"
    db_session.add(user)
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="production",
            email="prod@example.com",
        )
    )
    db_session.commit()
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project, environment="production")
    assert set(recipients) == {user.email, "prod@example.com"}


def test_get_project_alert_settings_uses_environment_override_for_teams(db_session, project_with_owner):
    """When owner is Teams/Teams Pro and env row exists, return env-level enabled/cooldown."""
    project, user = project_with_owner
    user.plan = "Teams"
    db_session.add(user)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=30,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="staging",
            enabled=False,
            cooldown_minutes=5,
        )
    )
    db_session.commit()
    enabled, level_filter, cooldown = get_project_alert_settings(
        db_session, project.id, environment="staging"
    )
    assert enabled is False
    assert cooldown == 5


def test_should_send_alert_disabled(db_session, project_with_owner):
    """When alerts disabled, should_send_alert returns False."""
    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(project_id=project.id, enabled=False)
    )
    db_session.commit()
    assert should_send_alert(db_session, project.id, "fp1", "error") is False


def test_should_send_alert_level_mismatch(db_session, project_with_owner):
    """When level does not match level_filter, returns False."""
    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
        )
    )
    db_session.commit()
    assert should_send_alert(db_session, project.id, "fp1", "warning") is False


def test_should_send_alert_no_cooldown(db_session, project_with_owner):
    """When cooldown is None, should_send_alert returns True (no cooldown row updated)."""
    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=None,
        )
    )
    db_session.commit()
    assert should_send_alert(db_session, project.id, "fp1", "error") is True


def test_should_send_alert_cooldown_first_send(db_session, project_with_owner):
    """First send for fingerprint returns True and records cooldown."""
    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=60,
        )
    )
    db_session.commit()
    assert should_send_alert(db_session, project.id, "fp1", "error") is True
    row = db_session.execute(
        select(models.AlertCooldown).where(
            models.AlertCooldown.project_id == project.id,
            models.AlertCooldown.fingerprint == "fp1",
        )
    ).scalars().first()
    assert row is not None


def test_should_send_alert_cooldown_blocks_second_send(db_session, project_with_owner):
    """When cooldown row exists and within cooldown window, returns False."""
    from datetime import timedelta, timezone
    from datetime import datetime as dt

    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=60,
        )
    )
    now = dt.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.AlertCooldown(
            project_id=project.id,
            fingerprint="fp1",
            last_notified_at=now - timedelta(minutes=5),
        )
    )
    db_session.commit()
    assert should_send_alert(db_session, project.id, "fp1", "error") is False


def test_should_send_alert_project_level_cooldown_blocks_other_fingerprint(db_session, project_with_owner):
    """Project-level cooldown: no email for any issue if project had a send in the last cooldown_minutes."""
    from datetime import timedelta, timezone
    from datetime import datetime as dt

    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=10,
        )
    )
    now = dt.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.AlertCooldown(
            project_id=project.id,
            fingerprint="fp_other",
            last_notified_at=now - timedelta(minutes=2),
        )
    )
    db_session.commit()
    # Same project, different fingerprint: still blocked by project-level cooldown
    assert should_send_alert(db_session, project.id, "fp_new", "error") is False


def test_should_send_alert_cooldown_10min_persists_after_restart(db_session, project_with_owner):
    """With 10 min cooldown set, email is not sent before 10 mins even after server restart (new session)."""
    import xrayradar_server.db as dbmod

    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=10,
        )
    )
    db_session.commit()

    # First send: allowed, creates AlertCooldown row and commits
    assert should_send_alert(db_session, project.id, "fp1", "error") is True

    # Simulate server restart: new DB session (as would happen after restart)
    db2 = dbmod.SessionLocal()
    try:
        # Immediately after "restart", same project/fingerprint: must not send (still within 10 min)
        assert should_send_alert(db2, project.id, "fp1", "error") is False
    finally:
        db2.close()


def test_should_send_alert_cooldown_expired_updates_timestamp(db_session, project_with_owner):
    """When cooldown row exists but expired, returns True and updates last_notified_at."""
    from datetime import timedelta, timezone
    from datetime import datetime as dt

    project, _ = project_with_owner
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=10,  # 10 minute cooldown
        )
    )
    old_time = dt.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=15)
    db_session.add(
        models.AlertCooldown(
            project_id=project.id,
            fingerprint="fp2",
            last_notified_at=old_time,
        )
    )
    db_session.commit()

    # Cooldown has expired, should return True and update
    result = should_send_alert(db_session, project.id, "fp2", "error")
    assert result is True

    # Verify timestamp was updated
    row = db_session.execute(
        select(models.AlertCooldown).where(
            models.AlertCooldown.project_id == project.id,
            models.AlertCooldown.fingerprint == "fp2",
        )
    ).scalars().first()
    assert row is not None
    assert row.last_notified_at > old_time


def test_get_last_alert_sent_at_returns_latest_success(db_session, project_with_owner):
    project, _ = project_with_owner
    db_session.add(
        models.EmailLog(
            email_type="error_alert",
            recipient_email="a@x.com",
            project_id=project.id,
            success=True,
        )
    )
    db_session.add(
        models.EmailLog(
            email_type="error_alert",
            recipient_email="a@x.com",
            project_id=project.id,
            success=False,
        )
    )
    db_session.commit()
    latest = get_last_alert_sent_at(
        db_session,
        project_id=project.id,
        recipient_email="a@x.com",
    )
    assert latest is not None


def test_get_top_issues_since_returns_top_5_and_scopes_environment(db_session, project_with_owner):
    project, _ = project_with_owner
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [
        ("fp1", "prod msg 1", "production"),
        ("fp1", "prod msg 2", "production"),
        ("fp1", "prod msg 3", "production"),
        ("fp2", "stg msg 1", "staging"),
        ("fp2", "stg msg 2", "staging"),
        ("fp3", "prod msg 4", "production"),
        ("fp4", "prod msg 5", "production"),
        ("fp5", "prod msg 6", "production"),
        ("fp6", "prod msg 7", "production"),
    ]
    for idx, (fp, msg, env) in enumerate(rows):
        db_session.add(
            models.Event(
                project_id=project.id,
                timestamp=now - timedelta(minutes=20 - idx),
                level="error",
                message=msg,
                environment=env,
                release=None,
                server_name=None,
                fingerprint=fp,
                payload={"message": msg},
            )
        )
    db_session.commit()

    top = get_top_issues_since(
        db_session,
        project_id=project.id,
        start=now - timedelta(hours=1),
        end=now,
        environment="production",
        limit=5,
    )
    assert len(top) == 5
    assert top[0]["fingerprint"] == "fp1"
    assert all(item["environment"] == "production" for item in top)
