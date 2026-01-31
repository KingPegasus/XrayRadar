"""Tests for notifications module (email alerts)"""

import sys
import uuid
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select

from xrayradar_server import models
from xrayradar_server.notifications import (
    get_project_alert_settings,
    get_alert_recipients,
    should_send_alert,
    send_alert_emails,
)


@pytest.fixture
def db_session(database_url):
    import xrayradar_server.db as dbmod
    dbmod.init_db()
    db = dbmod.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def project_with_owner(db_session):
    """Create a user and project owned by that user. Unique email per test to avoid UNIQUE constraint."""
    email = f"owner-{uuid.uuid4().hex}@example.com"
    user = models.User(
        email=email,
        password_hash="hash",
        plan="Free",
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


def test_get_alert_recipients_owner_only(db_session, project_with_owner):
    """Recipients include owner email when no additional recipients."""
    project, user = project_with_owner
    # Ensure owner is loaded
    project = db_session.get(models.Project, project.id)
    recipients = get_alert_recipients(db_session, project)
    assert set(recipients) == {user.email}


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


def test_send_alert_emails_no_recipients():
    """send_alert_emails with empty list does nothing."""
    send_alert_emails(
        recipients=[],
        project_name="P",
        event_message="msg",
        event_id=uuid.uuid4(),
        project_id=1,
        fingerprint="fp",
    )


def test_send_alert_emails_resend_not_configured():
    """When RESEND_API_KEY unset, send_alert_emails does not raise."""
    with patch("xrayradar_server.notifications.RESEND_API_KEY", ""):
        send_alert_emails(
            recipients=["a@x.com"],
            project_name="P",
            event_message="msg",
            event_id=uuid.uuid4(),
            project_id=1,
            fingerprint="fp",
        )


def test_send_alert_emails_mock_resend():
    """send_alert_emails calls Resend when configured; exceptions are caught."""
    # Mock resend module so import resend succeeds without the package installed
    mock_resend = MagicMock()
    mock_resend.Emails.send = MagicMock(return_value={"id": "123"})
    with patch.dict("sys.modules", {"resend": mock_resend}):
        with patch("xrayradar_server.notifications.RESEND_API_KEY", "key"):
            with patch("xrayradar_server.notifications.RESEND_FROM_EMAIL", "from@x.com"):
                send_alert_emails(
                    recipients=["a@x.com"],
                    project_name="P",
                    event_message="msg",
                    event_id=uuid.uuid4(),
                    project_id=1,
                    fingerprint="fp",
                )
                mock_resend.Emails.send.assert_called_once()
                call_args = mock_resend.Emails.send.call_args[0][0]
                assert call_args["to"] == ["a@x.com"]
                assert "P" in call_args["subject"]
                assert "msg" in call_args["html"]


def test_send_alert_emails_resend_raises_swallowed():
    """When Resend.Emails.send raises, exception is caught and not propagated."""
    mock_resend = MagicMock()
    mock_resend.Emails.send = MagicMock(side_effect=RuntimeError("Resend API error"))
    with patch.dict("sys.modules", {"resend": mock_resend}):
        with patch("xrayradar_server.notifications.RESEND_API_KEY", "key"):
            with patch("xrayradar_server.notifications.RESEND_FROM_EMAIL", "from@x.com"):
                send_alert_emails(
                    recipients=["a@x.com"],
                    project_name="P",
                    event_message="msg",
                    event_id=uuid.uuid4(),
                    project_id=1,
                    fingerprint="fp",
                )
    # No exception raised
    mock_resend.Emails.send.assert_called_once()
