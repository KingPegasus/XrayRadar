"""Durable email job queue and worker."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .constants import ADMIN_EMAILS, RESEND_API_KEY, RESEND_FROM_EMAIL, XRAYRADAR_BASE_URL
from .db import SessionLocal
from .email_templates import (
    render_admin_new_user_email,
    render_admin_token_request_email,
    render_error_digest_email,
    render_password_reset_email,
    render_post_verification_getting_started_email,
    render_team_invite_email,
    render_verification_email,
)
from .email_log import log_email
from .models import AlertScheduleState, EmailJob
from .notifications import get_last_alert_sent_at, get_top_issues_since

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


def enqueue_admin_new_user_email(
    db: Session, *, user_email: str, plan: str, user_id: int, signed_up_at: datetime
) -> EmailJob | None:
    if not ADMIN_EMAILS:
        return None
    return enqueue_email_job(
        db,
        "admin_new_user",
        {
            "recipient_emails": ADMIN_EMAILS,
            "user_email": user_email,
            "plan": plan,
            "user_id": user_id,
            "signed_up_at": signed_up_at.isoformat(),
        },
    )


def enqueue_admin_token_request_email(
    db: Session,
    *,
    user_email: str,
    request_name: str,
    request_note: str | None,
    request_id: int,
    requested_at: datetime,
) -> EmailJob | None:
    if not ADMIN_EMAILS:
        return None
    return enqueue_email_job(
        db,
        "admin_token_request",
        {
            "recipient_emails": ADMIN_EMAILS,
            "user_email": user_email,
            "request_name": request_name,
            "request_note": request_note or "",
            "request_id": request_id,
            "requested_at": requested_at.isoformat(),
        },
    )


def _send_via_resend(
    *,
    to_email: str | None = None,
    to_emails: list[str] | None = None,
    subject: str,
    html: str,
) -> None:
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        raise RuntimeError("Resend not configured")
    import resend

    recipients = list(to_emails or [])
    if to_email:
        recipients.append(to_email)
    recipients = sorted({str(e).strip().lower() for e in recipients if str(e).strip()})
    if not recipients:
        raise RuntimeError("Missing recipient_email")

    resend.api_key = RESEND_API_KEY
    resend.Emails.send(
        {
            "from": RESEND_FROM_EMAIL,
            "to": recipients,
            "subject": subject,
            "html": html,
        }
    )


def _deliver_job(db: Session, job: EmailJob) -> None:
    payload = job.payload or {}
    job_type = job.job_type
    recipient = str(payload.get("recipient_email") or "").strip().lower()

    if job_type == "error_alert":
        payload_recipients = payload.get("recipient_emails") or []
        recipients = sorted(
            {
                str(e).strip().lower()
                for e in payload_recipients
                if isinstance(e, str) and str(e).strip()
            }
        )
        if recipient:
            recipients.append(recipient)
        recipients = sorted(set(recipients))
        if not recipients:
            raise RuntimeError("Missing recipient_email")

        project_name = str(payload.get("project_name") or "Project")
        project_id = int(payload.get("project_id") or 0)
        environment = str(payload.get("environment") or "").strip()
        trigger_raw = str(payload.get("triggered_at") or "").strip()
        try:
            window_end = datetime.fromisoformat(trigger_raw) if trigger_raw else datetime.now(timezone.utc).replace(tzinfo=None)
        except Exception:  # noqa: BLE001
            window_end = datetime.now(timezone.utc).replace(tzinfo=None)
        # Dedupe: if we already sent a digest for this project+env very recently, skip (avoids duplicate emails from race).
        env_key = (environment or "").strip()
        state_row = (
            db.execute(
                select(AlertScheduleState).where(
                    AlertScheduleState.project_id == project_id,
                    AlertScheduleState.environment == env_key,
                )
            )
            .scalars()
            .first()
        )
        if state_row is not None and state_row.last_sent_at is not None:
            delta_seconds = abs((window_end - state_row.last_sent_at).total_seconds())
            if delta_seconds < 90:
                return
        sent_ats = [
            get_last_alert_sent_at(
                db,
                project_id=project_id,
                recipient_email=email,
            )
            for email in recipients
        ]
        window_start = max((t for t in sent_ats if t is not None), default=None)
        issues = get_top_issues_since(
            db,
            project_id=project_id,
            start=window_start,
            end=window_end,
            environment=environment or None,
        )
        # Skip sending empty digests (e.g. duplicate job with stale window).
        if not issues:
            return

        subject, html = render_error_digest_email(
            base_url=XRAYRADAR_BASE_URL,
            project_name=project_name,
            project_id=project_id,
            environment=environment or None,
            window_start=window_start,
            window_end=window_end,
            issues=issues,
        )
        _send_via_resend(to_emails=recipients, subject=subject, html=html)
        for email in recipients:
            log_email(
                db,
                "error_alert",
                email,
                success=True,
                project_id=project_id or None,
            )
        state_to_update = state_row
        if state_to_update is None:
            state_to_update = (
                db.execute(
                    select(AlertScheduleState).where(
                        AlertScheduleState.project_id == project_id,
                        AlertScheduleState.environment == env_key,
                    )
                )
                .scalars()
                .first()
            )
        if state_to_update is not None:
            state_to_update.last_sent_at = window_end
            db.add(state_to_update)
        return

    if job_type == "admin_new_user":
        recipients = sorted(
            {
                str(e).strip().lower()
                for e in (payload.get("recipient_emails") or [])
                if isinstance(e, str) and str(e).strip()
            }
        )
        if not recipients:
            raise RuntimeError("Missing recipient_email")
        user_email = str(payload.get("user_email") or "").strip().lower()
        plan = str(payload.get("plan") or "").strip() or "Free"
        user_id = int(payload.get("user_id") or 0)
        signed_up_raw = str(payload.get("signed_up_at") or "").strip()
        try:
            signed_up_at = (
                datetime.fromisoformat(signed_up_raw)
                if signed_up_raw
                else datetime.now(timezone.utc).replace(tzinfo=None)
            )
        except Exception:  # noqa: BLE001
            signed_up_at = datetime.now(timezone.utc).replace(tzinfo=None)
        subject, html = render_admin_new_user_email(
            base_url=XRAYRADAR_BASE_URL,
            user_email=user_email,
            plan=plan,
            user_id=user_id,
            signed_up_at=signed_up_at,
        )
        _send_via_resend(to_emails=recipients, subject=subject, html=html)
        for email in recipients:
            log_email(db, "admin_new_user", email, success=True, user_id=user_id or None)
        return

    if job_type == "admin_token_request":
        recipients = sorted(
            {
                str(e).strip().lower()
                for e in (payload.get("recipient_emails") or [])
                if isinstance(e, str) and str(e).strip()
            }
        )
        if not recipients:
            raise RuntimeError("Missing recipient_emails")
        user_email = str(payload.get("user_email") or "").strip().lower()
        request_name = str(payload.get("request_name") or "").strip() or "—"
        request_note = (payload.get("request_note") or "").strip() or None
        request_id = int(payload.get("request_id") or 0)
        requested_raw = str(payload.get("requested_at") or "").strip()
        try:
            requested_at = (
                datetime.fromisoformat(requested_raw)
                if requested_raw
                else datetime.now(timezone.utc).replace(tzinfo=None)
            )
        except Exception:  # noqa: BLE001
            requested_at = datetime.now(timezone.utc).replace(tzinfo=None)
        subject, html = render_admin_token_request_email(
            base_url=XRAYRADAR_BASE_URL,
            user_email=user_email,
            request_name=request_name,
            request_note=request_note,
            request_id=request_id,
            requested_at=requested_at,
        )
        _send_via_resend(to_emails=recipients, subject=subject, html=html)
        for email in recipients:
            log_email(db, "admin_token_request", email, success=True, user_id=None)
        return

    if not recipient:
        raise RuntimeError("Missing recipient_email")

    if job_type == "verification":
        token = str(payload.get("token") or "").strip()
        user_id = payload.get("user_id")
        subject, html = render_verification_email(base_url=XRAYRADAR_BASE_URL, token=token)
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "verification", recipient, success=True, user_id=user_id)
        return

    if job_type == "password_reset":
        token = str(payload.get("token") or "").strip()
        user_id = payload.get("user_id")
        subject, html = render_password_reset_email(base_url=XRAYRADAR_BASE_URL, token=token)
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "password_reset", recipient, success=True, user_id=user_id)
        return

    if job_type == "team_invite":
        invite_token = str(payload.get("invite_token") or "").strip()
        inviter_email = str(payload.get("inviter_email") or "").strip()
        user_id = payload.get("user_id")
        subject, html = render_team_invite_email(
            base_url=XRAYRADAR_BASE_URL,
            invite_token=invite_token,
            inviter_email=inviter_email,
        )
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "team_invite", recipient, success=True, user_id=user_id)
        return

    if job_type == "post_verification_onboarding":
        user_id = payload.get("user_id")
        subject, html = render_post_verification_getting_started_email(
            base_url=XRAYRADAR_BASE_URL,
        )
        _send_via_resend(to_email=recipient, subject=subject, html=html)
        log_email(db, "post_verification_onboarding", recipient, success=True, user_id=user_id)
        return

    raise RuntimeError(f"Unknown email job type: {job_type}")


def process_pending_email_jobs(limit: int = 25) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = SessionLocal()
    try:
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
        except OperationalError as e:
            if "no such table" in str(e).lower() and "email_jobs" in str(e).lower():
                return
            raise
        for job in jobs:
            payload = job.payload or {}
            recipient = payload.get("recipient_email")
            if recipient is None and payload.get("recipient_emails"):
                recipient = f"{len(payload.get('recipient_emails', []))} recipients"
            logger.info(
                "Processing email job: job_id=%s type=%s recipient=%s",
                job.id,
                job.job_type,
                recipient,
            )
            try:
                _deliver_job(db, job)
                job.status = "sent"
                job.processed_at = now
                job.last_error = None
                logger.info(
                    "Email sent: job_id=%s type=%s recipient=%s",
                    job.id,
                    job.job_type,
                    recipient,
                )
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
                raw_payload = job.payload or {}
                recipients = {
                    str((raw_payload).get("recipient_email") or "").strip().lower()
                }
                recipients.update(
                    {
                        str(e).strip().lower()
                        for e in ((raw_payload).get("recipient_emails") or [])
                        if isinstance(e, str) and str(e).strip()
                    }
                )
                recipients.discard("")
                if recipients:
                    project_id = (job.payload or {}).get("project_id")
                    for recipient in recipients:
                        log_email(
                            db,
                            job.job_type,
                            recipient,
                            success=False,
                            project_id=int(project_id) if isinstance(project_id, int) else None,
                            error_message=str(e),
                        )
            db.add(job)
            db.commit()
    finally:
        db.close()

