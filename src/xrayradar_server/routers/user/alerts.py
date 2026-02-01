"""User API: alert settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...constants import MAX_ALERT_RECIPIENTS, MIN_COOLDOWN_MINUTES_BY_PLAN
from ...db import get_db
from ...models import ProjectAlertRecipient, ProjectAlertSettings, User
from ...deps import require_user, require_verified_user
from ...schemas import AlertSettingsOut, AlertSettingsUpdate
from ._helpers import require_owned_project

router = APIRouter()


@router.get("/api/user/projects/{project_id}/alert-settings", response_model=AlertSettingsOut)
def user_get_alert_settings(
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get email alert settings for the project (owned by current user)."""
    require_owned_project(db, user=user, project_id=project_id)
    min_cooldown = MIN_COOLDOWN_MINUTES_BY_PLAN.get(user.plan, 10)
    settings = db.get(ProjectAlertSettings, project_id)
    if settings is None:
        return AlertSettingsOut(
            enabled=False,
            level_filter="error",
            cooldown_minutes=None,
            min_cooldown_minutes=min_cooldown,
            additional_emails=[],
        )
    recipients = (
        db.execute(
            select(ProjectAlertRecipient.email).where(
                ProjectAlertRecipient.project_id == project_id
            )
        )
        .scalars().all()
    )
    additional_emails = [r for r in recipients if r]
    cooldown = settings.cooldown_minutes
    if cooldown is not None and min_cooldown is not None and cooldown < min_cooldown:
        cooldown = min_cooldown
    return AlertSettingsOut(
        enabled=settings.enabled,
        level_filter=settings.level_filter or "error",
        cooldown_minutes=cooldown,
        min_cooldown_minutes=min_cooldown,
        additional_emails=additional_emails,
    )


@router.patch("/api/user/projects/{project_id}/alert-settings", response_model=AlertSettingsOut)
def user_update_alert_settings(
    project_id: int,
    payload: AlertSettingsUpdate,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Update email alert settings and additional recipients (full replace for additional_emails)."""
    require_owned_project(db, user=user, project_id=project_id)
    min_cooldown = MIN_COOLDOWN_MINUTES_BY_PLAN.get(user.plan, 10)
    if payload.cooldown_minutes is not None and payload.cooldown_minutes > 0:
        if payload.cooldown_minutes < min_cooldown:
            raise HTTPException(
                status_code=400,
                detail=f"Cooldown minimum for your plan is {min_cooldown} minutes.",
            )
    settings = db.get(ProjectAlertSettings, project_id)
    if settings is None:
        settings = ProjectAlertSettings(project_id=project_id)
        db.add(settings)
    if payload.enabled is not None:
        settings.enabled = payload.enabled
    if payload.level_filter is not None:
        settings.level_filter = payload.level_filter
    if payload.cooldown_minutes is not None:
        settings.cooldown_minutes = payload.cooldown_minutes
    if payload.additional_emails is not None:
        if len(payload.additional_emails) > MAX_ALERT_RECIPIENTS:
            raise HTTPException(
                status_code=400,
                detail=f"At most {MAX_ALERT_RECIPIENTS} additional emails allowed.",
            )
        seen: set[str] = set()
        normalized: list[str] = []
        for e in payload.additional_emails:
            if not e or not isinstance(e, str):
                continue
            s = e.strip().lower()
            if s and s not in seen:
                seen.add(s)
                normalized.append(s)
        for row in db.execute(
            select(ProjectAlertRecipient).where(
                ProjectAlertRecipient.project_id == project_id
            )
        ).scalars().all():
            db.delete(row)
        for email in normalized:
            db.add(ProjectAlertRecipient(project_id=project_id, email=email))
    db.commit()
    db.refresh(settings)
    return user_get_alert_settings(project_id=project_id, user=user, db=db)
