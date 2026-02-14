import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from xrayradar_server import models
from xrayradar_server.mail_jobs import (
    MAX_ATTEMPTS,
    _deliver_job,
    enqueue_email_job,
    process_pending_email_jobs,
)


@pytest.fixture
def db_session(database_url, monkeypatch):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    import xrayradar_server.db as dbmod

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


def _create_project_with_owner(db):
    email = f"owner-{uuid.uuid4().hex}@test.com"
    user = models.User(email=email, password_hash="h", plan="Basic")
    db.add(user)
    db.commit()
    db.refresh(user)
    project = models.Project(name="Project One", owner_user_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_error_alert_job_builds_digest_and_logs_success(db_session, monkeypatch):
    project = _create_project_with_owner(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.EmailLog(
            email_type="error_alert",
            recipient_email="a@test.com",
            project_id=project.id,
            success=True,
            sent_at=now - timedelta(minutes=30),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(minutes=10),
            level="error",
            message="Database timeout",
            environment="production",
            release=None,
            server_name=None,
            fingerprint="fp-db-timeout",
            payload={"message": "Database timeout"},
        )
    )
    db_session.commit()

    sent = {}

    def _fake_send(*, to_email=None, to_emails=None, subject, html):
        sent["to_email"] = to_email
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["html"] = html

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="error_alert",
        payload={
            "recipient_emails": ["a@test.com"],
            "project_name": project.name,
            "project_id": project.id,
            "environment": "production",
            "triggered_at": now.isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    _deliver_job(db_session, job)

    assert sent["to_email"] is None
    assert sent["to_emails"] == ["a@test.com"]
    assert "Error digest" in sent["subject"]
    assert "Database timeout" in sent["html"]
    logs = db_session.execute(
        select(models.EmailLog).where(
            models.EmailLog.email_type == "error_alert",
            models.EmailLog.project_id == project.id,
            models.EmailLog.recipient_email == "a@test.com",
        )
    ).scalars().all()
    assert any(log.success is True for log in logs)


def test_enqueue_email_job_returns_job(db_session):
    job = enqueue_email_job(
        db_session,
        "verification",
        {"recipient_email": "u@test.com", "token": "t", "user_id": 1},
    )
    assert job.id is not None
    assert job.job_type == "verification"
    assert job.status == "pending"
    assert job.attempts == 0


def test_send_via_resend_raises_when_not_configured(monkeypatch):
    from xrayradar_server.mail_jobs import _send_via_resend

    monkeypatch.setattr("xrayradar_server.mail_jobs.RESEND_API_KEY", "")
    monkeypatch.setattr("xrayradar_server.mail_jobs.RESEND_FROM_EMAIL", "")
    with pytest.raises(RuntimeError, match="Resend not configured"):
        _send_via_resend(to_email="a@x.com", subject="s", html="h")


def test_deliver_job_verification(db_session, monkeypatch):
    sent = {}

    def _fake_send(*, to_email, subject, html):
        sent["to_email"] = to_email
        sent["subject"] = subject

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="verification",
        payload={"recipient_email": "verify@test.com", "token": "abc123", "user_id": 1},
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_email"] == "verify@test.com"
    assert "verify" in sent["subject"].lower()


def test_deliver_job_password_reset(db_session, monkeypatch):
    sent = {}

    def _fake_send(*, to_email, subject, html):
        sent["to_email"] = to_email

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="password_reset",
        payload={"recipient_email": "reset@test.com", "token": "xyz", "user_id": 2},
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_email"] == "reset@test.com"


def test_deliver_job_team_invite(db_session, monkeypatch):
    sent = {}

    def _fake_send(*, to_email, subject, html):
        sent["to_email"] = to_email
        sent["html"] = html

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="team_invite",
        payload={
            "recipient_email": "invite@test.com",
            "invite_token": "tok",
            "inviter_email": "owner@test.com",
            "user_id": 1,
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_email"] == "invite@test.com"
    assert "accept" in sent["html"].lower()


def test_deliver_job_missing_recipient_raises(db_session):
    job = models.EmailJob(
        job_type="verification",
        payload={"token": "t"},
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    with pytest.raises(RuntimeError, match="Missing recipient_email"):
        _deliver_job(db_session, job)


def test_deliver_job_error_alert_skips_empty_digest(db_session, monkeypatch):
    """Empty digest (no issues in window) is not sent - avoids duplicate empty emails."""
    project = _create_project_with_owner(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.EmailLog(
            email_type="error_alert",
            recipient_email="a@test.com",
            project_id=project.id,
            success=True,
            sent_at=now - timedelta(minutes=5),
        )
    )
    # No events in the window (last_sent_at=5min ago to now); get_top_issues_since returns []
    db_session.commit()

    sent_called = []

    def _fake_send(**kw):
        sent_called.append(1)

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="error_alert",
        payload={
            "recipient_emails": ["a@test.com"],
            "project_name": project.name,
            "project_id": project.id,
            "environment": "",
            "triggered_at": now.isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    _deliver_job(db_session, job)

    assert sent_called == [], "should not send when digest has no issues"


def test_deliver_job_unknown_type_raises(db_session):
    job = models.EmailJob(
        job_type="unknown_type",
        payload={"recipient_email": "a@test.com"},
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    with pytest.raises(RuntimeError, match="Unknown email job type"):
        _deliver_job(db_session, job)


def test_deliver_job_error_alert_invalid_triggered_at_uses_now(db_session, monkeypatch):
    project = _create_project_with_owner(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(minutes=5),
            level="error",
            message="err",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp",
            payload={"message": "err"},
        )
    )
    sent = {}

    def _fake_send(*, to_email=None, to_emails=None, subject, html):
        sent["to_emails"] = to_emails
        sent["subject"] = subject

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="error_alert",
        payload={
            "recipient_emails": ["a@test.com"],
            "project_name": project.name,
            "project_id": project.id,
            "environment": "",
            "triggered_at": "not-a-valid-datetime",
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_emails"] == ["a@test.com"]
    assert "digest" in sent["subject"].lower()


def test_deliver_error_alert_to_multiple_recipients_logs_each(db_session, monkeypatch):
    project = _create_project_with_owner(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(minutes=5),
            level="error",
            message="err",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp",
            payload={"message": "err"},
        )
    )
    sent = {}

    def _fake_send(*, to_email=None, to_emails=None, subject, html):
        sent["to_emails"] = to_emails
        sent["subject"] = subject

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="error_alert",
        payload={
            "recipient_emails": ["a@test.com", "b@test.com", "A@test.com"],
            "project_name": project.name,
            "project_id": project.id,
            "environment": "",
            "triggered_at": now.isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    _deliver_job(db_session, job)

    assert sent["to_emails"] == ["a@test.com", "b@test.com"]
    logs = db_session.execute(
        select(models.EmailLog).where(
            models.EmailLog.email_type == "error_alert",
            models.EmailLog.project_id == project.id,
        )
    ).scalars().all()
    assert {log.recipient_email for log in logs if log.success is True} >= {"a@test.com", "b@test.com"}


class _NoCloseSession:
    def __init__(self, session):
        self._session = session
    def close(self):
        pass
    def __getattr__(self, name):
        return getattr(self._session, name)


def test_process_pending_email_jobs_sends_and_marks_sent(db_session, monkeypatch):
    _create_project_with_owner(db_session)
    # Isolate from other tests: mark any existing pending jobs so only ours is processed
    db_session.execute(update(models.EmailJob).where(models.EmailJob.status == "pending").values(status="sent"))
    db_session.commit()
    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", lambda **kw: None)
    job = enqueue_email_job(
        db_session,
        "verification",
        {"recipient_email": "p@test.com", "token": "t", "user_id": 1},
    )
    monkeypatch.setattr("xrayradar_server.mail_jobs.SessionLocal", lambda: _NoCloseSession(db_session))
    process_pending_email_jobs(limit=10)
    db_session.expire_all()
    job = db_session.get(models.EmailJob, job.id)
    assert job is not None
    assert job.status == "sent"
    assert job.processed_at is not None


def test_process_pending_email_jobs_failure_increments_attempts_and_backoff(db_session, monkeypatch):
    db_session.execute(update(models.EmailJob).where(models.EmailJob.status == "pending").values(status="sent"))
    db_session.commit()
    def _fail_send(**kw):
        raise RuntimeError("Resend error")

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fail_send)
    job = enqueue_email_job(
        db_session,
        "verification",
        {"recipient_email": "fail@test.com", "token": "t", "user_id": 1},
    )
    monkeypatch.setattr("xrayradar_server.mail_jobs.SessionLocal", lambda: _NoCloseSession(db_session))
    process_pending_email_jobs(limit=10)
    db_session.expire_all()
    job = db_session.get(models.EmailJob, job.id)
    assert job is not None
    assert job.attempts == 1
    assert job.status == "pending"
    assert job.next_attempt_at is not None
    assert job.last_error == "Resend error"


def test_process_pending_email_jobs_max_attempts_marks_failed(db_session, monkeypatch):
    db_session.execute(update(models.EmailJob).where(models.EmailJob.status == "pending").values(status="sent"))
    db_session.commit()
    def _fail_send(**kw):
        raise RuntimeError("Resend error")

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fail_send)
    job = enqueue_email_job(
        db_session,
        "verification",
        {"recipient_email": "max@test.com", "token": "t", "user_id": 1},
    )
    job_id = job.id
    monkeypatch.setattr("xrayradar_server.mail_jobs.SessionLocal", lambda: _NoCloseSession(db_session))
    for _ in range(MAX_ATTEMPTS + 1):
        j = db_session.get(models.EmailJob, job_id)
        if j is None:
            break
        if j.status == "failed":
            break
        if j.status == "pending":
            j.next_attempt_at = None
            db_session.add(j)
            db_session.commit()
        process_pending_email_jobs(limit=10)
        db_session.expire_all()
    job = db_session.get(models.EmailJob, job_id)
    assert job is not None
    assert job.status == "failed"
    assert job.attempts >= MAX_ATTEMPTS
    assert job.processed_at is not None
