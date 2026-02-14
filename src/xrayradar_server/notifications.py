"""Email alert settings and digest data helpers."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .models import (
    AlertCooldown,
    EmailLog,
    Event,
    Project,
    ProjectAlertEnvironmentRecipient,
    ProjectAlertEnvironmentSetting,
    ProjectAlertRecipient,
    ProjectAlertSettings,
    User,
)

def get_project_alert_settings(
    db: Session, project_id: int, environment: str | None = None
) -> tuple[bool, str, int | None]:
    """Return (enabled, level_filter, cooldown_minutes) for the project. Defaults if no row."""
    row = db.get(ProjectAlertSettings, project_id)
    enabled = False if row is None else row.enabled
    level_filter = "error" if row is None else row.level_filter
    cooldown = None if row is None else row.cooldown_minutes
    env = (environment or "").strip()
    if env:
        env_row = (
            db.execute(
                select(ProjectAlertEnvironmentSetting).where(
                    ProjectAlertEnvironmentSetting.project_id == project_id,
                    ProjectAlertEnvironmentSetting.environment == env,
                )
            )
            .scalars()
            .first()
        )
        if env_row is not None:
            enabled = env_row.enabled
            if env_row.cooldown_minutes is not None:
                cooldown = env_row.cooldown_minutes
    return enabled, level_filter, cooldown


def get_alert_recipients(db: Session, project: Project, environment: str | None = None) -> list[str]:
    """Combine owner email and additional recipients, deduplicated. Returns [] for Free plan (no alerts)."""
    if project.owner_user_id is not None:
        owner = db.get(User, project.owner_user_id)
        if owner is not None and owner.plan == "Free":
            return []
    emails: set[str] = set()
    if project.owner_user_id is not None:
        owner = db.get(User, project.owner_user_id)
        if owner is not None:
            emails.add(owner.email)
    recs = (
        db.execute(
            select(ProjectAlertRecipient.email).where(
                ProjectAlertRecipient.project_id == project.id
            )
        )
        .scalars().all()
    )
    for r in recs:
        # Handle both scalar (str) and Row/tuple from different SQLAlchemy result shapes
        val = r[0] if (isinstance(r, (tuple, list)) or (hasattr(r, "__getitem__") and not isinstance(r, str))) else r
        emails.add(val)
    env = (environment or "").strip()
    if env:
        env_recs = (
            db.execute(
                select(ProjectAlertEnvironmentRecipient.email).where(
                    ProjectAlertEnvironmentRecipient.project_id == project.id,
                    ProjectAlertEnvironmentRecipient.environment == env,
                )
            )
            .scalars()
            .all()
        )
        for r in env_recs:
            if isinstance(r, str) and r.strip():
                emails.add(r.strip().lower())
    return list(emails)


def should_send_alert(
    db: Session, project_id: int, fingerprint: str | None, level: str, environment: str | None = None
) -> bool:
    """Return True if alerts are enabled, level matches, and cooldown allows. Updates cooldown when sending."""
    enabled, level_filter, cooldown_minutes = get_project_alert_settings(db, project_id, environment=environment)
    if not enabled or level != level_filter:
        return False
    fp = fingerprint or ""
    if cooldown_minutes is None or cooldown_minutes <= 0:
        return True
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cooldown_delta = timedelta(minutes=cooldown_minutes) + timedelta(seconds=1)
    project_max = db.execute(
        select(func.max(AlertCooldown.last_notified_at)).where(
            AlertCooldown.project_id == project_id,
        )
    ).scalar()
    if project_max is not None and now < project_max + cooldown_delta:
        return False
    row = db.execute(
        select(AlertCooldown).where(
            AlertCooldown.project_id == project_id,
            AlertCooldown.fingerprint == fp,
        )
    ).scalars().first()
    if row is not None:
        cooldown = row[0] if isinstance(row, tuple) else row
        if now < cooldown.last_notified_at + cooldown_delta:
            return False
        cooldown.last_notified_at = now
    else:
        db.add(
            AlertCooldown(
                project_id=project_id,
                fingerprint=fp,
                last_notified_at=now,
            )
        )
    db.commit()
    return True


def get_last_alert_sent_at(
    db: Session,
    *,
    project_id: int,
    recipient_email: str,
) -> datetime | None:
    """Return most recent successful error_alert send time for recipient+project."""
    recipient = (recipient_email or "").strip().lower()
    if not recipient:
        return None
    return db.execute(
        select(func.max(EmailLog.sent_at)).where(
            EmailLog.email_type == "error_alert",
            EmailLog.success.is_(True),
            EmailLog.project_id == project_id,
            EmailLog.recipient_email == recipient,
        )
    ).scalar()


def get_top_issues_since(
    db: Session,
    *,
    project_id: int,
    start: datetime | None,
    end: datetime,
    environment: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """
    Return top issues in [start, end] window ordered by frequency.

    Each item includes fingerprint, count, latest_timestamp, latest_message, and environment.
    """
    predicates = [Event.project_id == project_id, Event.timestamp <= end]
    if start is not None:
        predicates.append(Event.timestamp > start)
    env = (environment or "").strip()
    if env:
        predicates.append(Event.environment == env)

    grouped = (
        db.execute(
            select(
                Event.fingerprint,
                func.count(Event.id).label("event_count"),
                func.max(Event.timestamp).label("latest_timestamp"),
            )
            .where(and_(*predicates))
            .group_by(Event.fingerprint)
            .order_by(func.count(Event.id).desc(), func.max(Event.timestamp).desc())
            .limit(limit)
        )
        .all()
    )

    items: list[dict] = []
    for fp, event_count, latest_timestamp in grouped:
        latest_event = (
            db.execute(
                select(Event)
                .where(
                    Event.project_id == project_id,
                    Event.fingerprint == fp,
                    Event.timestamp == latest_timestamp,
                )
                .order_by(Event.id.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        items.append(
            {
                "fingerprint": fp or "",
                "count": int(event_count or 0),
                "latest_timestamp": latest_timestamp,
                "latest_message": (latest_event.message if latest_event else "")[:300],
                "environment": (latest_event.environment if latest_event else None),
            }
        )
    return items
