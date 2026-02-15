from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import select

from xrayradar_server import models
from xrayradar_server.alert_scheduler import (
    ENQUEUE_DEBOUNCE_SECONDS,
    enqueue_error_alert_job,
    evaluate_due_alerts,
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
        db.query(models.EmailJob).delete()
        db.query(models.EmailLog).delete()
        db.query(models.AlertScheduleState).delete()
        db.query(models.AlertCooldown).delete()
        db.query(models.ProjectAlertEnvironmentRecipient).delete()
        db.query(models.ProjectAlertEnvironmentSetting).delete()
        db.query(models.ProjectAlertRecipient).delete()
        db.query(models.ProjectAlertSettings).delete()
        db.query(models.Event).delete()
        db.query(models.Project).delete()
        db.query(models.User).delete()
        db.commit()
        yield db
    finally:
        db.close()


def _create_project(db):
    user = models.User(email=f"owner-{uuid.uuid4().hex}@example.com", password_hash="h", plan="Basic")
    db.add(user)
    db.commit()
    db.refresh(user)
    project = models.Project(name="P", owner_user_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _set_project_owner_plan(db, project, plan):
    owner = db.get(models.User, project.owner_user_id)
    assert owner is not None
    owner.plan = plan
    db.add(owner)
    db.commit()


def test_scheduler_enqueues_when_cooldown_elapsed_and_new_events_exist(db_session):
    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=3),
            last_evaluated_at=now - timedelta(minutes=2),
            last_event_seen_at=now - timedelta(minutes=3),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=20),
            level="error",
            message="new error",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp1",
            payload={"message": "new error"},
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 1
    jobs = db_session.execute(
        select(models.EmailJob).where(
            models.EmailJob.job_type == "error_alert",
            models.EmailJob.status == "pending",
        )
    ).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].payload.get("project_id") == project.id


def test_scheduler_does_not_enqueue_when_no_new_events(db_session):
    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=3),
            last_evaluated_at=now - timedelta(minutes=2),
            last_event_seen_at=now - timedelta(minutes=1),
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 0
    jobs = db_session.execute(select(models.EmailJob)).scalars().all()
    assert jobs == []


def test_scheduler_dedupes_repeated_runs_same_window(db_session):
    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=5),
            level="error",
            message="error",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp2",
            payload={"message": "error"},
        )
    )
    db_session.commit()

    first = evaluate_due_alerts(now=now)
    second = evaluate_due_alerts(now=now)
    assert first == 1
    assert second == 0

    jobs = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().all()
    assert len(jobs) == 1


def test_scheduler_enqueues_environment_specific_scope(db_session):
    project = _create_project(db_session)
    _set_project_owner_plan(db_session, project, "Teams")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=False,
            level_filter="error",
            cooldown_minutes=5,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="production",
            enabled=True,
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="production",
            email="alerts@example.com",
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="production",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=10),
            level="error",
            message="prod error",
            environment="production",
            release=None,
            server_name=None,
            fingerprint="fp3",
            payload={"message": "prod error"},
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 1
    job = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().first()
    assert job is not None
    assert job.payload.get("environment") == "production"


def test_enqueue_debounce_prevents_ingest_scheduler_duplicate(db_session):
    """Ingest and scheduler within 90s should only enqueue once."""
    from xrayradar_server.notifications import get_alert_recipients

    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=10),
            level="error",
            message="err",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp-debounce",
            payload={"message": "err"},
        )
    )
    db_session.commit()

    recipients = get_alert_recipients(db_session, project, environment=None)
    assert recipients

    t1 = now
    t2 = now + timedelta(seconds=30)  # 30s later (within 90s debounce)

    first = enqueue_error_alert_job(
        db_session,
        project=project,
        recipients=recipients,
        environment=None,
        triggered_at=t1,
    )
    second = enqueue_error_alert_job(
        db_session,
        project=project,
        recipients=recipients,
        environment=None,
        triggered_at=t2,
    )

    assert first is True
    assert second is False  # debounced

    jobs = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().all()
    assert len(jobs) == 1


def test_enqueue_after_debounce_window_succeeds(db_session):
    """After 90s debounce, a new enqueue is allowed."""
    from xrayradar_server.notifications import get_alert_recipients

    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_enqueued_at=now - timedelta(seconds=ENQUEUE_DEBOUNCE_SECONDS + 10),
            last_job_key="error_alert:1:all:old",
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=5),
            level="error",
            message="err",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp-after",
            payload={"message": "err"},
        )
    )
    db_session.commit()

    recipients = get_alert_recipients(db_session, project, environment=None)
    assert recipients

    ok = enqueue_error_alert_job(
        db_session,
        project=project,
        recipients=recipients,
        environment=None,
        triggered_at=now,
    )
    assert ok is True


def test_enqueue_error_alert_job_no_recipients_returns_false(db_session):
    """enqueue_error_alert_job returns False when recipients list is empty."""
    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ok = enqueue_error_alert_job(
        db_session,
        project=project,
        recipients=[],
        environment=None,
        triggered_at=now,
    )
    assert ok is False
    jobs = db_session.execute(select(models.EmailJob)).scalars().all()
    assert len(jobs) == 0


def test_enqueue_error_alert_job_stores_event_seen_at(db_session):
    """enqueue_error_alert_job stores event_seen_at on state when provided."""
    from xrayradar_server.notifications import get_alert_recipients

    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=10),
            level="error",
            message="e",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp-es",
            payload={"message": "e"},
        )
    )
    db_session.commit()
    recipients = get_alert_recipients(db_session, project, environment=None)
    assert recipients
    event_seen = now - timedelta(seconds=10)
    enqueue_error_alert_job(
        db_session,
        project=project,
        recipients=recipients,
        environment=None,
        triggered_at=now,
        event_seen_at=event_seen,
    )
    from xrayradar_server.models import AlertScheduleState
    state = db_session.execute(
        select(AlertScheduleState).where(
            AlertScheduleState.project_id == project.id,
            AlertScheduleState.environment == "",
        )
    ).scalars().first()
    assert state is not None
    assert state.last_event_seen_at == event_seen


def test_scheduler_project_scope_excludes_events_owned_by_enabled_env_scope(db_session):
    project = _create_project(db_session)
    _set_project_owner_plan(db_session, project, "Teams")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="development",
            enabled=True,
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="development",
            email="dev@example.com",
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="development",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=10),
            level="error",
            message="dev only",
            environment="development",
            release=None,
            server_name=None,
            fingerprint="fp-dev",
            payload={"message": "dev only"},
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 1
    jobs = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].payload.get("environment") == "development"


def test_scheduler_project_scope_still_includes_events_without_environment(db_session):
    project = _create_project(db_session)
    _set_project_owner_plan(db_session, project, "Teams")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="development",
            enabled=True,
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="development",
            email="dev@example.com",
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=15),
            level="error",
            message="no env",
            environment=None,
            release=None,
            server_name=None,
            fingerprint="fp-none",
            payload={"message": "no env"},
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 1
    job = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().first()
    assert job is not None
    assert job.payload.get("environment") is None


def test_scheduler_project_scope_includes_events_for_env_without_own_config(db_session):
    project = _create_project(db_session)
    _set_project_owner_plan(db_session, project, "Teams")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="development",
            enabled=True,
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="development",
            email="dev@example.com",
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=10),
            level="error",
            message="staging err",
            environment="staging",
            release=None,
            server_name=None,
            fingerprint="fp-staging",
            payload={"message": "staging err"},
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 1
    job = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().first()
    assert job is not None
    assert job.payload.get("environment") is None


def test_scheduler_ignores_environment_scopes_for_basic_plan(db_session):
    project = _create_project(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        models.ProjectAlertSettings(
            project_id=project.id,
            enabled=True,
            level_filter="error",
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentSetting(
            project_id=project.id,
            environment="development",
            enabled=True,
            cooldown_minutes=1,
        )
    )
    db_session.add(
        models.ProjectAlertEnvironmentRecipient(
            project_id=project.id,
            environment="development",
            email="dev@example.com",
        )
    )
    db_session.add(
        models.AlertScheduleState(
            project_id=project.id,
            environment="",
            last_sent_at=now - timedelta(minutes=10),
            last_evaluated_at=now - timedelta(minutes=9),
            last_event_seen_at=now - timedelta(minutes=10),
        )
    )
    db_session.add(
        models.Event(
            project_id=project.id,
            timestamp=now - timedelta(seconds=10),
            level="error",
            message="dev only",
            environment="development",
            release=None,
            server_name=None,
            fingerprint="fp-dev-basic",
            payload={"message": "dev only"},
        )
    )
    db_session.commit()

    enqueued = evaluate_due_alerts(now=now)
    assert enqueued == 1
    jobs = db_session.execute(
        select(models.EmailJob).where(models.EmailJob.job_type == "error_alert")
    ).scalars().all()
    assert len(jobs) == 1
    # Basic users get project-level digests only (no environment-scoped email)
    assert jobs[0].payload.get("environment") is None

