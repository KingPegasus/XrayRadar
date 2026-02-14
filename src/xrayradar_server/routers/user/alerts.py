"""User API: alert settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...constants import MAX_ALERT_RECIPIENTS, MIN_COOLDOWN_MINUTES_BY_PLAN
from ...db import get_db
from ...models import (
    ProjectAlertEnvironmentRecipient,
    ProjectAlertEnvironmentSetting,
    ProjectAlertRecipient,
    ProjectAlertSettings,
    User,
)
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
    min_cooldown = MIN_COOLDOWN_MINUTES_BY_PLAN.get(user.plan)
    if user.plan == "Free":
        return AlertSettingsOut(
            enabled=False,
            level_filter="error",
            cooldown_minutes=None,
            min_cooldown_minutes=None,
            additional_emails=[],
            environment_settings=[],
        )
    min_cooldown = MIN_COOLDOWN_MINUTES_BY_PLAN.get(user.plan, 10)
    settings = db.get(ProjectAlertSettings, project_id)
    if settings is None:
        return AlertSettingsOut(
            enabled=False,
            level_filter="error",
            cooldown_minutes=None,
            min_cooldown_minutes=min_cooldown,
            additional_emails=[],
            environment_settings=[],
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
    env_settings_rows = (
        db.execute(
            select(ProjectAlertEnvironmentSetting).where(
                ProjectAlertEnvironmentSetting.project_id == project_id
            )
        )
        .scalars()
        .all()
    )
    env_rec_rows = (
        db.execute(
            select(ProjectAlertEnvironmentRecipient).where(
                ProjectAlertEnvironmentRecipient.project_id == project_id
            )
        )
        .scalars()
        .all()
    )
    by_env_recipients: dict[str, list[str]] = {}
    for row in env_rec_rows:
        by_env_recipients.setdefault(row.environment, []).append(row.email)
    env_settings = [
        {
            "environment": row.environment,
            "enabled": row.enabled,
            "cooldown_minutes": row.cooldown_minutes,
            "additional_emails": sorted(set(by_env_recipients.get(row.environment, []))),
        }
        for row in env_settings_rows
    ]
    cooldown = settings.cooldown_minutes
    if cooldown is not None and min_cooldown is not None and cooldown < min_cooldown:
        cooldown = min_cooldown
    return AlertSettingsOut(
        enabled=settings.enabled,
        level_filter=settings.level_filter or "error",
        cooldown_minutes=cooldown,
        min_cooldown_minutes=min_cooldown,
        additional_emails=additional_emails,
        environment_settings=env_settings,
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
    if user.plan == "Free":
        if payload.enabled:
            raise HTTPException(
                status_code=400,
                detail="Email alerts are not available on the Free plan. Upgrade to Basic, Teams, or Teams Pro.",
            )
        min_cooldown = None
    else:
        min_cooldown = MIN_COOLDOWN_MINUTES_BY_PLAN.get(user.plan, 10)
    if min_cooldown is not None and payload.cooldown_minutes is not None and payload.cooldown_minutes > 0:
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
    if payload.environment_settings is not None:
        existing_env_settings = (
            db.execute(
                select(ProjectAlertEnvironmentSetting).where(
                    ProjectAlertEnvironmentSetting.project_id == project_id
                )
            )
            .scalars()
            .all()
        )
        for row in existing_env_settings:
            db.delete(row)
        existing_env_recipients = (
            db.execute(
                select(ProjectAlertEnvironmentRecipient).where(
                    ProjectAlertEnvironmentRecipient.project_id == project_id
                )
            )
            .scalars()
            .all()
        )
        for row in existing_env_recipients:
            db.delete(row)
        for item in payload.environment_settings:
            if not isinstance(item, dict):
                continue
            env = str(item.get("environment") or "").strip()
            if not env:
                continue
            env_enabled = bool(item.get("enabled", True))
            env_cooldown = item.get("cooldown_minutes")
            if env_cooldown is not None:
                try:
                    env_cooldown = int(env_cooldown)
                except Exception:  # noqa: BLE001
                    env_cooldown = None
            db.add(
                ProjectAlertEnvironmentSetting(
                    project_id=project_id,
                    environment=env,
                    enabled=env_enabled,
                    cooldown_minutes=env_cooldown,
                )
            )
            env_emails = item.get("additional_emails")
            if isinstance(env_emails, list):
                seen_env: set[str] = set()
                for e in env_emails:
                    if not isinstance(e, str):
                        continue
                    normalized_email = e.strip().lower()
                    if normalized_email and normalized_email not in seen_env:
                        seen_env.add(normalized_email)
                        db.add(
                            ProjectAlertEnvironmentRecipient(
                                project_id=project_id,
                                environment=env,
                                email=normalized_email,
                            )
                        )
    db.commit()
    db.refresh(settings)
    return user_get_alert_settings(project_id=project_id, user=user, db=db)
