"""Durable email job queue and worker."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import RESEND_API_KEY, RESEND_FROM_EMAIL, XRAYRADAR_BASE_URL
from .db import SessionLocal
from .email_log import log_email
from .models import EmailJob

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


def enqueue_email_job(db: Session, job_type: str, payload: dict) -> EmailJob:
    job = EmailJob(
        job_type=job_type,
        payload=payload,
        status="pending",
        attempts=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _send_via_resend(*, to_email: str, subject: str, html: str) -> None:
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        raise RuntimeError("Resend not configured")
    import resend

    resend.api_key = RESEND_API_KEY
    resend.Emails.send(
        {
            "from": RESEND_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
    )


def _deliver_job(db: Session, job: EmailJob) -> None:
    payload = job.payload or {}
    job_type = job.job_type
    recipient = str(payload.get("recipient_email") or "").strip().lower()
    if not recipient:
        raise RuntimeError("Missing recipient_email")

    if job_type == "error_alert":
        project_name = str(payload.get("project_name") or "Project")
        event_message = str(payload.get("event_message") or "New error")
        project_id = int(payload.get("project_id") or 0)
        fingerprint = str(payload.get("fingerprint") or "").strip()
        issue_path = f"/dashboard/projects/{project_id}/issues"
        if fingerprint:
            issue_path = f"/dashboard/projects/{project_id}/issues/{fingerprint}"
        link = f"{XRAYRADAR_BASE_URL.rstrip('/')}{issue_path}"
        environment = str(payload.get("environment") or "").strip()
        env_label = f" [{environment}]" if environment else ""
        subject = f"[XrayRadar]{env_label} {project_name}: {event_message[:80]}"
        html = (
            f"<p>New error in <b>{project_name}</b>{env_label}.</p>"
            f"<p>{event_message}</p>"
            f"<p><a href=\"{link}\">View in XrayRadar</a></p>"
        )
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(
            db,
            "error_alert",
            recipient,
            success=True,
            project_id=project_id or None,
        )
        return

    if job_type == "verification":
        token = str(payload.get("token") or "").strip()
        user_id = payload.get("user_id")
        verify_link = f"{XRAYRADAR_BASE_URL.rstrip('/')}/verify-email?token={token}"
        subject = "[XrayRadar] Verify your email address"
        html = (
            "<p>Welcome to XrayRadar!</p>"
            "<p>Please verify your email address by clicking the link below:</p>"
            f"<p><a href=\"{verify_link}\">Verify Email</a></p>"
            "<p>This link will expire in 24 hours.</p>"
        )
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "verification", recipient, success=True, user_id=user_id)
        return

    if job_type == "password_reset":
        token = str(payload.get("token") or "").strip()
        user_id = payload.get("user_id")
        reset_link = f"{XRAYRADAR_BASE_URL.rstrip('/')}/reset-password?token={token}"
        subject = "[XrayRadar] Reset your password"
        html = (
            "<p>You requested a password reset for your XrayRadar account.</p>"
            f"<p><a href=\"{reset_link}\">Reset Password</a></p>"
            "<p>This link will expire in 1 hour.</p>"
        )
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "password_reset", recipient, success=True, user_id=user_id)
        return

    if job_type == "team_invite":
        invite_token = str(payload.get("invite_token") or "").strip()
        inviter_email = str(payload.get("inviter_email") or "").strip()
        user_id = payload.get("user_id")
        accept_url = f"{XRAYRADAR_BASE_URL.rstrip('/')}/accept-invite?token={invite_token}"
        subject = "You're invited to join a team on Xrayradar"
        html = (
            f"<p>You've been invited by {inviter_email} to join their team on Xrayradar.</p>"
            f"<p><a href=\"{accept_url}\">Accept invite</a></p>"
            "<p>This link expires in 7 days.</p>"
        )
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "team_invite", recipient, success=True, user_id=user_id)
        return

    raise RuntimeError(f"Unknown email job type: {job_type}")


def process_pending_email_jobs(limit: int = 25) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = SessionLocal()
    try:
        jobs = (
            db.execute(
                select(EmailJob)
                .where(EmailJob.status == "pending")
                .where(
                    (EmailJob.next_attempt_at.is_(None))
                    | (EmailJob.next_attempt_at <= now)
                )
                .order_by(EmailJob.created_at.asc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        for job in jobs:
            try:
                _deliver_job(db, job)
                job.status = "sent"
                job.processed_at = now
                job.last_error = None
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to process email job %s: %s", job.id, e)
                job.attempts = int(job.attempts or 0) + 1
                job.last_error = str(e)
                if job.attempts >= MAX_ATTEMPTS:
                    job.status = "failed"
                    job.processed_at = now
                else:
                    backoff_minutes = min(30, 2 ** max(0, job.attempts - 1))
                    job.next_attempt_at = now + timedelta(minutes=backoff_minutes)
                # Log failed email attempt if recipient is present.
                recipient = str((job.payload or {}).get("recipient_email") or "").strip().lower()
                if recipient:
                    log_email(db, job.job_type, recipient, success=False, error_message=str(e))
            db.add(job)
            db.commit()
    finally:
        db.close()

