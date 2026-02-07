"""Utility for logging email send attempts to the EmailLog table."""

from sqlalchemy.orm import Session

from .models import EmailLog


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
    except Exception:  # noqa: BLE001
        db.rollback()
