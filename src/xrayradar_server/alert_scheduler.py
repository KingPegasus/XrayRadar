"""Periodic alert scheduler for cooldown-based digest enqueues."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import db as dbmod
from .mail_jobs import enqueue_email_job, process_pending_email_jobs
from .models import (
    AlertScheduleState,
    Event,
    Project,
    ProjectAlertEnvironmentSetting,
    ProjectAlertSettings,
)
from .notifications import get_alert_recipients, get_project_alert_settings


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _env_key(environment: str | None) -> str:
    return (environment or "").strip()


def _ensure_state(
    db: Session,
    *,
    project_id: int,
    environment: str | None,
) -> AlertScheduleState:
    env = _env_key(environment)
    stmt = select(AlertScheduleState).where(
        AlertScheduleState.project_id == project_id,
        AlertScheduleState.environment == env,
    )
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    state = db.execute(stmt).scalars().first()
    if state is not None:
        return state
    state = AlertScheduleState(project_id=project_id, environment=env)
    db.add(state)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        state = (
            db.execute(
                select(AlertScheduleState).where(
                    AlertScheduleState.project_id == project_id,
                    AlertScheduleState.environment == env,
                )
            )
            .scalars()
            .first()
        )
        if state is None:
            raise
    return state


def _build_job_key(*, project_id: int, environment: str | None, triggered_at: datetime) -> str:
    env = _env_key(environment) or "all"
    bucket = triggered_at.strftime("%Y%m%d%H%M")
    return f"error_alert:{project_id}:{env}:{bucket}"


# Debounce window: do not enqueue a second job if we already enqueued recently.
# Covers ingest + scheduler overlap (scheduler runs every 60s) without delaying normal alerts.
ENQUEUE_DEBOUNCE_SECONDS = 90


def enqueue_error_alert_job(
    db: Session,
    *,
    project: Project,
    recipients: list[str],
    environment: str | None,
    triggered_at: datetime | None = None,
    event_seen_at: datetime | None = None,
) -> bool:
    """Enqueue deduped error_alert job for the project/environment scope."""
    if not recipients:
        return False
    when = triggered_at or _utcnow_naive()
    state = _ensure_state(db, project_id=project.id, environment=environment)
    job_key = _build_job_key(project_id=project.id, environment=environment, triggered_at=when)
    if state.last_job_key == job_key:
        return False
    # Prevent ingest and scheduler from both enqueueing when they run close together.
    if state.last_enqueued_at is not None:
        delta = (when - state.last_enqueued_at).total_seconds()
        if delta < ENQUEUE_DEBOUNCE_SECONDS:
            return False

    enqueue_email_job(
        db,
        "error_alert",
        {
            "job_key": job_key,
            "recipient_emails": recipients,
            "project_name": project.name,
            "project_id": project.id,
            "environment": _env_key(environment) or None,
            "triggered_at": when.isoformat(),
        },
    )
    state.last_job_key = job_key
    state.last_evaluated_at = when
    state.last_enqueued_at = when
    if event_seen_at is not None:
        state.last_event_seen_at = event_seen_at
    db.add(state)
    db.commit()
    return True


def _evaluate_scope(
    db: Session,
    *,
    project: Project,
    environment: str | None,
    now: datetime,
) -> bool:
    enabled, level_filter, cooldown_minutes = get_project_alert_settings(
        db, project.id, environment=environment
    )
    if not enabled:
        return False
    recipients = get_alert_recipients(db, project, environment=environment)
    if not recipients:
        return False

    state = _ensure_state(db, project_id=project.id, environment=environment)
    start = state.last_sent_at or state.last_event_seen_at

    # Initial bootstrap: do not backfill old history before scheduler existed.
    if state.last_sent_at is None and state.last_event_seen_at is None and state.last_evaluated_at is None:
        bootstrap_predicates = [Event.project_id == project.id, Event.level == level_filter]
        env = _env_key(environment)
        if env:
            bootstrap_predicates.append(Event.environment == env)
        latest_seen = db.execute(
            select(func.max(Event.timestamp)).where(and_(*bootstrap_predicates))
        ).scalar()
        state.last_evaluated_at = now
        state.last_event_seen_at = latest_seen
        db.add(state)
        db.commit()
        return False

    if cooldown_minutes is not None and cooldown_minutes > 0 and state.last_sent_at is not None:
        due_at = state.last_sent_at + timedelta(minutes=cooldown_minutes) + timedelta(seconds=1)
        if now < due_at:
            state.last_evaluated_at = now
            db.add(state)
            db.commit()
            return False

    predicates = [Event.project_id == project.id, Event.level == level_filter, Event.timestamp <= now]
    if start is not None:
        predicates.append(Event.timestamp > start)
    env = _env_key(environment)
    if env:
        predicates.append(Event.environment == env)
    row = db.execute(
        select(func.count(Event.id), func.max(Event.timestamp)).where(and_(*predicates))
    ).one()
    count = int(row[0] or 0)
    latest_seen = row[1]

    state.last_evaluated_at = now
    if latest_seen is not None:
        state.last_event_seen_at = latest_seen
    db.add(state)
    db.commit()

    if count <= 0:
        return False

    return enqueue_error_alert_job(
        db,
        project=project,
        recipients=recipients,
        environment=environment,
        triggered_at=now,
        event_seen_at=latest_seen,
    )


def evaluate_due_alerts(limit_projects: int = 200, now: datetime | None = None) -> int:
    """Evaluate project scopes and enqueue due alert jobs. Returns enqueue count."""
    now_ts = now or _utcnow_naive()
    db = dbmod.SessionLocal()
    try:
        project_ids = {
            int(pid)
            for pid in db.execute(
                select(ProjectAlertSettings.project_id).where(ProjectAlertSettings.enabled.is_(True))
            ).scalars().all()
        }
        project_ids.update(
            {
                int(pid)
                for pid in db.execute(
                    select(ProjectAlertEnvironmentSetting.project_id).where(
                        ProjectAlertEnvironmentSetting.enabled.is_(True)
                    )
                ).scalars().all()
            }
        )
        enqueued = 0
        for project_id in sorted(project_ids)[: max(1, limit_projects)]:
            project = db.get(Project, project_id)
            if project is None:
                continue

            if _evaluate_scope(db, project=project, environment=None, now=now_ts):
                enqueued += 1

            env_rows = (
                db.execute(
                    select(ProjectAlertEnvironmentSetting.environment).where(
                        ProjectAlertEnvironmentSetting.project_id == project_id,
                        ProjectAlertEnvironmentSetting.enabled.is_(True),
                    )
                )
                .scalars()
                .all()
            )
            for env in sorted({e.strip() for e in env_rows if isinstance(e, str) and e.strip()}):
                if _evaluate_scope(db, project=project, environment=env, now=now_ts):
                    enqueued += 1
        return enqueued
    finally:
        db.close()


def run_once(limit_projects: int = 200, job_limit: int = 100) -> dict[str, int]:
    """Run scheduler evaluate pass and process pending email jobs."""
    enqueued = evaluate_due_alerts(limit_projects=limit_projects)
    process_pending_email_jobs(limit=job_limit)
    return {"enqueued_jobs": enqueued}

