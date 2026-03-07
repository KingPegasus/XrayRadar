import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from xrayradar_server import models
from xrayradar_server.mail_jobs import (
    MAX_ATTEMPTS,
    _deliver_job,
    enqueue_admin_new_user_email,
    enqueue_admin_token_request_email,
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


def test_deliver_job_post_verification_onboarding(db_session, monkeypatch):
    sent = {}

    def _fake_send(*, to_email, subject, html):
        sent["to_email"] = to_email
        sent["subject"] = subject
        sent["html"] = html

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="post_verification_onboarding",
        payload={"recipient_email": "new@test.com", "user_id": 9},
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_email"] == "new@test.com"
    assert "getting started" in sent["subject"].lower()
    assert "Create your first project" in sent["html"]
    logs = db_session.execute(
        select(models.EmailLog).where(
            models.EmailLog.email_type == "post_verification_onboarding",
            models.EmailLog.recipient_email == "new@test.com",
            models.EmailLog.success.is_(True),
        )
    ).scalars().all()
    assert len(logs) >= 1


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


def test_deliver_job_error_alert_skips_duplicate_within_90_seconds(db_session, monkeypatch):
    """Second digest for same project+env within 90s is skipped to avoid duplicate emails."""
    project = _create_project_with_owner(db_session)
    owner = db_session.get(models.User, project.owner_user_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_end = now
    last_sent = now - timedelta(seconds=30)
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="development",
            last_sent_at=last_sent,
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(minutes=5),
            level="error",
            message="err",
            environment="development",
            release=None,
            server_name=None,
            fingerprint="fp",
            payload={"message": "err"},
        )
    )
    db_session.commit()

    sent_called = []

    def _fake_send(**kw):
        sent_called.append(1)

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    job = models.EmailJob(
        job_type="error_alert",
        payload={
            "recipient_emails": [owner.email],
            "project_name": project.name,
            "project_id": project.id,
            "environment": "development",
            "triggered_at": window_end.isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    _deliver_job(db_session, job)

    assert sent_called == [], "should not send when we already sent for this project+env within 90s"


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


def test_enqueue_admin_new_user_email_returns_none_when_no_admin_emails(db_session, monkeypatch):
    """When ADMIN_EMAILS is empty, enqueue_admin_new_user_email returns None and creates no job."""
    monkeypatch.setattr("xrayradar_server.mail_jobs.ADMIN_EMAILS", [])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = enqueue_admin_new_user_email(
        db_session,
        user_email="u@test.com",
        plan="Free",
        user_id=1,
        signed_up_at=now,
    )
    assert result is None
    jobs = db_session.execute(select(models.EmailJob).where(models.EmailJob.job_type == "admin_new_user")).scalars().all()
    assert len(jobs) == 0


def test_enqueue_admin_new_user_email_creates_job_when_admin_emails_set(db_session, monkeypatch):
    """When ADMIN_EMAILS is set, enqueue_admin_new_user_email creates an admin_new_user job with correct payload."""
    monkeypatch.setattr("xrayradar_server.mail_jobs.ADMIN_EMAILS", ["admin@test.com"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    job = enqueue_admin_new_user_email(
        db_session,
        user_email="newuser@test.com",
        plan="Teams",
        user_id=99,
        signed_up_at=now,
    )
    assert job is not None
    assert job.job_type == "admin_new_user"
    assert job.status == "pending"
    payload = job.payload or {}
    assert payload.get("recipient_emails") == ["admin@test.com"]
    assert payload.get("user_email") == "newuser@test.com"
    assert payload.get("plan") == "Teams"
    assert payload.get("user_id") == 99
    assert payload.get("signed_up_at") == now.isoformat()


def test_deliver_job_admin_new_user(db_session, monkeypatch):
    """admin_new_user job sends to recipient_emails and logs each recipient."""
    sent = {}

    def _fake_send(*, to_email=None, to_emails=None, subject, html):
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["html"] = html

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    job = models.EmailJob(
        job_type="admin_new_user",
        payload={
            "recipient_emails": ["admin1@test.com", "admin2@test.com"],
            "user_email": "signup@test.com",
            "plan": "Basic",
            "user_id": 7,
            "signed_up_at": now.isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_emails"] == ["admin1@test.com", "admin2@test.com"]
    assert "New user signup" in sent["subject"]
    assert "signup@test.com" in sent["html"]
    assert "Basic" in sent["html"]
    assert "7" in sent["html"]
    logs = db_session.execute(
        select(models.EmailLog).where(
            models.EmailLog.email_type == "admin_new_user",
            models.EmailLog.success.is_(True),
        )
    ).scalars().all()
    assert {log.recipient_email for log in logs} >= {"admin1@test.com", "admin2@test.com"}


def test_deliver_job_admin_new_user_missing_recipient_emails_raises(db_session):
    """admin_new_user job with empty recipient_emails raises."""
    job = models.EmailJob(
        job_type="admin_new_user",
        payload={
            "recipient_emails": [],
            "user_email": "u@test.com",
            "plan": "Free",
            "user_id": 1,
            "signed_up_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    with pytest.raises(RuntimeError, match="Missing recipient_email"):
        _deliver_job(db_session, job)


def test_enqueue_admin_token_request_email_returns_none_when_no_admin_emails(db_session, monkeypatch):
    """When ADMIN_EMAILS is empty, enqueue_admin_token_request_email returns None and creates no job."""
    monkeypatch.setattr("xrayradar_server.mail_jobs.ADMIN_EMAILS", [])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = enqueue_admin_token_request_email(
        db_session,
        user_email="u@test.com",
        request_name="My token",
        request_note="For prod",
        request_id=3,
        requested_at=now,
    )
    assert result is None
    jobs = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "admin_token_request")
    ).scalars().all()
    assert len(jobs) == 0


def test_enqueue_admin_token_request_email_creates_job_when_admin_emails_set(db_session, monkeypatch):
    """When ADMIN_EMAILS is set, enqueue_admin_token_request_email creates an admin_token_request job."""
    monkeypatch.setattr("xrayradar_server.mail_jobs.ADMIN_EMAILS", ["admin@test.com"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    job = enqueue_admin_token_request_email(
        db_session,
        user_email="dev@test.com",
        request_name="SDK token",
        request_note="Backend",
        request_id=7,
        requested_at=now,
    )
    assert job is not None
    assert job.job_type == "admin_token_request"
    assert job.status == "pending"
    payload = job.payload or {}
    assert payload.get("recipient_emails") == ["admin@test.com"]
    assert payload.get("user_email") == "dev@test.com"
    assert payload.get("request_name") == "SDK token"
    assert payload.get("request_note") == "Backend"
    assert payload.get("request_id") == 7
    assert payload.get("requested_at") == now.isoformat()


def test_deliver_job_admin_token_request(db_session, monkeypatch):
    """admin_token_request job sends to recipient_emails and logs each recipient."""
    sent = {}

    def _fake_send(*, to_email=None, to_emails=None, subject, html):
        sent["to_emails"] = to_emails
        sent["subject"] = subject
        sent["html"] = html

    monkeypatch.setattr("xrayradar_server.mail_jobs._send_via_resend", _fake_send)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    job = models.EmailJob(
        job_type="admin_token_request",
        payload={
            "recipient_emails": ["admin@test.com"],
            "user_email": "dev@test.com",
            "request_name": "My token",
            "request_note": "For production",
            "request_id": 12,
            "requested_at": now.isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    _deliver_job(db_session, job)
    assert sent["to_emails"] == ["admin@test.com"]
    assert "Token request" in sent["subject"]
    assert "dev@test.com" in sent["html"]
    assert "My token" in sent["html"]
    assert "For production" in sent["html"]
    assert "12" in sent["html"]
    logs = db_session.execute(
        select(models.EmailLog).where(
            models.EmailLog.email_type == "admin_token_request",
            models.EmailLog.success.is_(True),
        )
    ).scalars().all()
    assert len(logs) >= 1
    assert any(log.recipient_email == "admin@test.com" for log in logs)


def test_deliver_job_admin_token_request_missing_recipient_emails_raises(db_session):
    """admin_token_request job with empty recipient_emails raises."""
    job = models.EmailJob(
        job_type="admin_token_request",
        payload={
            "recipient_emails": [],
            "user_email": "u@test.com",
            "request_name": "x",
            "request_note": "",
            "request_id": 1,
            "requested_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        },
        status="pending",
        attempts=0,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    with pytest.raises(RuntimeError, match="Missing recipient_email"):
        _deliver_job(db_session, job)


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
