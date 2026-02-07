"""Email alerts for error events: recipients, cooldown, and Resend sending."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .constants import RESEND_API_KEY, RESEND_FROM_EMAIL, XRAYRADAR_BASE_URL
from .db import SessionLocal
from .email_log import log_email
from .models import (
    AlertCooldown,
    Project,
    ProjectAlertRecipient,
    ProjectAlertSettings,
    User,
)

logger = logging.getLogger(__name__)


def get_project_alert_settings(
    db: Session, project_id: int
) -> tuple[bool, str, int | None]:
    """Return (enabled, level_filter, cooldown_minutes) for the project. Defaults if no row."""
    row = db.get(ProjectAlertSettings, project_id)
    if row is None:
        return False, "error", None
    return row.enabled, row.level_filter, row.cooldown_minutes


def get_alert_recipients(db: Session, project: Project) -> list[str]:
    """Combine owner email and additional recipients, deduplicated."""
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
    return list(emails)


def should_send_alert(
    db: Session, project_id: int, fingerprint: str | None, level: str
) -> bool:
    """Return True if alerts are enabled, level matches, and cooldown allows. Updates cooldown when sending."""
    enabled, level_filter, cooldown_minutes = get_project_alert_settings(db, project_id)
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


def send_alert_emails(
    *,
    recipients: list[str],
    project_name: str,
    event_message: str,
    event_id: uuid.UUID,
    project_id: int,
    fingerprint: str | None,
) -> None:
    """Send one email to all recipients via Resend. No-op if no recipients or RESEND_API_KEY unset. Swallows errors."""
    if not recipients:
        return
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        return
    
    db = SessionLocal()
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        issue_path = f"/dashboard/projects/{project_id}/issues"
        if fingerprint:
            issue_path = f"/dashboard/projects/{project_id}/issues/{fingerprint}"
        link = f"{XRAYRADAR_BASE_URL.rstrip('/')}{issue_path}"
        subject = f"[XrayRadar] {project_name}: {event_message[:80]}"
        html = f"<p>New error in <b>{project_name}</b>.</p><p>{event_message}</p><p><a href=\"{link}\">View in XrayRadar</a></p>"
        resend.Emails.send(
            {
                "from": RESEND_FROM_EMAIL,
                "to": recipients,
                "subject": subject,
                "html": html,
            }
        )
        # Log successful emails (one per recipient)
        for recipient in recipients:
            log_email(db, "error_alert", recipient, success=True, project_id=project_id)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to send alert emails: %s", e)
        # Log failed emails (one per recipient)
        for recipient in recipients:
            log_email(
                db,
                "error_alert",
                recipient,
                success=False,
                project_id=project_id,
                error_message=str(e),
            )
    finally:
        db.close()
