"""Utility for logging email send attempts to the EmailLog table."""

import logging
from sqlalchemy.orm import Session

from .models import EmailLog

logger = logging.getLogger(__name__)


def log_email(
    db: Session,
    email_type: str,
    recipient_email: str,
    success: bool,
    user_id: int | None = None,
    project_id: int | None = None,
    error_message: str | None = None,
) -> None:
    """Log an email send attempt to the EmailLog table. Swallows errors."""
    try:
        log_entry = EmailLog(
            email_type=email_type,
            recipient_email=recipient_email,
            user_id=user_id,
            project_id=project_id,
            success=success,
            error_message=error_message[:1000] if error_message else None,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning(
            "Failed to write email_log (email_type=%s, recipient=%s): %s",
            email_type,
            recipient_email[:50] if recipient_email else "",
            e,
            exc_info=True,
        )
