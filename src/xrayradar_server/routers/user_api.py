from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..constants import MAX_ALERT_RECIPIENTS, MIN_COOLDOWN_MINUTES_BY_PLAN
from ..db import get_db
from ..models import (
    DeletionRequest,
    Event,
    Project,
    ProjectAlertRecipient,
    ProjectAlertSettings,
    Token,
    TokenProjectAccess,
    TokenRequest,
    User,
)
from ..deps import require_user, require_verified_user
from ..schemas import (
    AlertSettingsOut,
    AlertSettingsUpdate,
    DeletionRequestCreate,
    DeletionRequestOut,
    IssueSummaryOut,
    TokenProjectAccessOut,
    TokenRequestCreate,
    TokenRequestOut,
    UsageOut,
    UserProjectCreate,
    UserProjectOut,
    UserTokenOut,
)
from ..usage import check_user_event_limit, get_user_event_count, is_near_limit

router = APIRouter()


def _require_owned_project(db: Session, *, user: User, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


def _require_user_token(db: Session, *, user: User, token_id: int) -> Token:
    row = db.get(Token, token_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Token not found")
    if row.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Token revoked")
    return row


@router.get("/api/user/projects", response_model=list[UserProjectOut])
def user_list_projects(user: User = Depends(require_user), db: Session = Depends(get_db)):
    q = select(Project).where(Project.owner_user_id == user.id).order_by(Project.id.asc())
    rows = db.execute(q).scalars().all()
    return [UserProjectOut(id=p.id, name=p.name) for p in rows]


@router.post("/api/user/projects", response_model=UserProjectOut)
def user_create_project(
    payload: UserProjectCreate,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    row = Project(name=payload.name, owner_user_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return UserProjectOut(id=row.id, name=row.name)


@router.get("/api/user/usage", response_model=UsageOut)
def user_get_usage(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get current event storage usage and limits for the authenticated user."""
    current_count, limit, is_exceeded = check_user_event_limit(
        db, user, raise_on_exceed=False
    )
    near_limit = is_near_limit(current_count, limit)

    percentage_used = None
    if limit is not None and limit > 0:
        percentage_used = min(100.0, (current_count / limit) * 100.0)

    return UsageOut(
        current_count=current_count,
        limit=limit,
        plan=user.plan,
        is_exceeded=is_exceeded,
        is_near_limit=near_limit,
        percentage_used=percentage_used,
    )


@router.get("/api/user/tokens", response_model=list[UserTokenOut])
def user_list_tokens(user: User = Depends(require_user), db: Session = Depends(get_db)):
    q = (
        select(Token)
        .where(Token.user_id == user.id)
        .order_by(Token.id.asc())
    )
    rows = db.execute(q).scalars().all()
    return [
        UserTokenOut(
            id=t.id,
            name=t.name,
            token=t.token,
            created_at=t.created_at,
            revoked_at=t.revoked_at,
        )
        for t in rows
    ]


@router.get(
    "/api/user/tokens/{token_id}/projects",
    response_model=list[TokenProjectAccessOut],
)
def user_list_token_projects(
    token_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    _require_user_token(db, user=user, token_id=token_id)
    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
        .where(TokenProjectAccess.revoked_at.is_(None))
        .order_by(TokenProjectAccess.project_id.asc())
    )
    rows = db.execute(q).scalars().all()
    return [
        TokenProjectAccessOut(
            id=r.id,
            token_id=r.token_id,
            project_id=r.project_id,
            created_at=r.created_at,
            revoked_at=r.revoked_at,
        )
        for r in rows
    ]


@router.post(
    "/api/user/tokens/{token_id}/projects/{project_id}/grant",
    response_model=dict,
)
def user_grant_project_access(
    token_id: int,
    project_id: int,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    _require_owned_project(db, user=user, project_id=project_id)
    _require_user_token(db, user=user, token_id=token_id)

    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
        .where(TokenProjectAccess.project_id == project_id)
        .order_by(TokenProjectAccess.id.desc())
    )
    access = db.execute(q).scalars().first()
    if access is None:
        access = TokenProjectAccess(token_id=token_id, project_id=project_id)
    else:
        access.revoked_at = None
    db.add(access)
    db.commit()
    return {"ok": True}


@router.get("/api/user/token-requests", response_model=list[TokenRequestOut])
def user_list_token_requests(user: User = Depends(require_user), db: Session = Depends(get_db)):
    q = (
        select(TokenRequest)
        .where(TokenRequest.user_id == user.id)
        .order_by(TokenRequest.id.desc())
    )
    rows = db.execute(q).scalars().all()
    return [
        TokenRequestOut(
            id=r.id,
            name=r.name,
            note=r.note,
            created_at=r.created_at,
            fulfilled_at=r.fulfilled_at,
            fulfilled_token_id=r.fulfilled_token_id,
        )
        for r in rows
    ]


@router.post("/api/user/token-requests", response_model=TokenRequestOut)
def user_create_token_request(
    payload: TokenRequestCreate,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    row = TokenRequest(user_id=user.id, name=payload.name, note=payload.note)
    db.add(row)
    db.commit()
    db.refresh(row)
    return TokenRequestOut(
        id=row.id,
        name=row.name,
        note=row.note,
        created_at=row.created_at,
        fulfilled_at=row.fulfilled_at,
        fulfilled_token_id=row.fulfilled_token_id,
    )


@router.get("/api/user/projects/{project_id}/issues", response_model=list[IssueSummaryOut])
def user_list_issues(
    project_id: int,
    limit: int = 50,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    _require_owned_project(db, user=user, project_id=project_id)

    clamped_limit = min(max(limit, 1), 200)
    agg = (
        select(
            Event.fingerprint,
            func.count(Event.id).label("count"),
            func.min(Event.timestamp).label("first_seen"),
            func.max(Event.timestamp).label("last_seen"),
        )
        .where(Event.project_id == project_id)
        .where(Event.fingerprint.is_not(None))
        .group_by(Event.fingerprint)
        .order_by(func.max(Event.timestamp).desc())
        .limit(clamped_limit)
    )
    groups = db.execute(agg).all()

    out: list[IssueSummaryOut] = []
    for fp, count, first_seen, last_seen in groups:
        q_latest = (
            select(Event)
            .where(Event.project_id == project_id)
            .where(Event.fingerprint == fp)
            .order_by(Event.timestamp.desc())
            .limit(1)
        )
        latest = db.execute(q_latest).scalars().first()
        if latest is None:
            continue
        out.append(
            IssueSummaryOut(
                fingerprint=str(fp),
                count=int(count or 0),
                first_seen=first_seen,
                last_seen=last_seen,
                level=latest.level,
                message=latest.message,
                environment=latest.environment,
                release=latest.release,
            )
        )
    return out


@router.get("/api/user/projects/{project_id}/alert-settings", response_model=AlertSettingsOut)
def user_get_alert_settings(
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get email alert settings for the project (owned by current user)."""
    project = _require_owned_project(db, user=user, project_id=project_id)
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
    # .scalars().all() returns list of scalar values (email strings), not tuples
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
    project = _require_owned_project(db, user=user, project_id=project_id)
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
        # Normalize and dedupe
        seen: set[str] = set()
        normalized: list[str] = []
        for e in payload.additional_emails:
            if not e or not isinstance(e, str):
                continue
            s = e.strip().lower()
            if s and s not in seen:
                seen.add(s)
                normalized.append(s)
        # Replace: delete existing, insert new
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


@router.get("/api/user/projects/{project_id}/events", response_model=list[dict])
def user_list_project_events(
    project_id: int,
    limit: int = 200,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """List events for a project (for frequency chart). Returns events from the last 30 days."""
    _require_owned_project(db, user=user, project_id=project_id)
    
    # Filter to last 30 days to ensure we have data for the full frequency chart range
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    clamped_limit = min(max(limit, 1), 500)
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .where(Event.timestamp >= thirty_days_ago)
        .order_by(Event.timestamp.desc())
        .limit(clamped_limit)
    )
    rows = db.execute(q).scalars().all()
    return [
        {
            "id": str(r.id),
            "timestamp": r.timestamp,
            "level": r.level,
            "message": r.message,
        }
        for r in rows
    ]


@router.get("/api/user/projects/{project_id}/events/frequency", response_model=dict)
def user_get_project_event_frequency(
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get event frequency counts per day for the last 30 days (for frequency chart).
    This uses aggregation to efficiently count all events without limit restrictions."""
    _require_owned_project(db, user=user, project_id=project_id)
    
    # Filter to last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Aggregate events by date (UTC date, ignoring time)
    # Use func.date() to extract just the date part for grouping
    q = (
        select(
            func.date(Event.timestamp).label("date"),
            func.count(Event.id).label("count"),
        )
        .where(Event.project_id == project_id)
        .where(Event.timestamp >= thirty_days_ago)
        .group_by(func.date(Event.timestamp))
        .order_by(func.date(Event.timestamp))
    )
    rows = db.execute(q).all()
    
    # Convert to dictionary with date strings as keys
    frequency = {}
    for date_obj, count in rows:
        # Convert date to ISO string (YYYY-MM-DD)
        if isinstance(date_obj, datetime):
            date_str = date_obj.date().isoformat()
        elif hasattr(date_obj, 'isoformat'):
            date_str = date_obj.isoformat()
        else:
            # Handle string dates or other formats
            date_str = str(date_obj)
            # If it's a datetime string, extract just the date part
            if ' ' in date_str or 'T' in date_str:
                date_str = date_str.split()[0].split('T')[0]
        frequency[date_str] = int(count or 0)
    
    # Get total count for the period
    total_q = (
        select(func.count(Event.id))
        .where(Event.project_id == project_id)
        .where(Event.timestamp >= thirty_days_ago)
    )
    total_count = db.execute(total_q).scalar() or 0
    
    return {
        "frequency": frequency,
        "total": total_count,
    }


@router.get(
    "/api/user/projects/{project_id}/issues/{fingerprint}/events/frequency",
    response_model=dict,
)
def user_get_issue_event_frequency(
    project_id: int,
    fingerprint: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get event frequency counts per day for a specific issue (last 30 days).
    This uses aggregation to efficiently count all events without limit restrictions."""
    _require_owned_project(db, user=user, project_id=project_id)
    
    # Filter to last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Aggregate events by date (UTC date, ignoring time)
    q = (
        select(
            func.date(Event.timestamp).label("date"),
            func.count(Event.id).label("count"),
        )
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
        .group_by(func.date(Event.timestamp))
        .order_by(func.date(Event.timestamp))
    )
    rows = db.execute(q).all()
    
    # Convert to dictionary with date strings as keys
    frequency = {}
    for date_obj, count in rows:
        # Convert date to ISO string (YYYY-MM-DD)
        if isinstance(date_obj, datetime):
            date_str = date_obj.date().isoformat()
        elif hasattr(date_obj, 'isoformat'):
            date_str = date_obj.isoformat()
        else:
            # Handle string dates or other formats
            date_str = str(date_obj)
            # If it's a datetime string, extract just the date part
            if ' ' in date_str or 'T' in date_str:
                date_str = date_str.split()[0].split('T')[0]
        frequency[date_str] = int(count or 0)
    
    # Get total count for the period
    total_q = (
        select(func.count(Event.id))
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
    )
    total_count = db.execute(total_q).scalar() or 0
    
    return {
        "frequency": frequency,
        "total": total_count,
    }


@router.get(
    "/api/user/projects/{project_id}/issues/{fingerprint}/events",
    response_model=list[dict],
)
def user_list_issue_events(
    project_id: int,
    fingerprint: str,
    limit: int = 50,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    _require_owned_project(db, user=user, project_id=project_id)
    clamped_limit = min(max(limit, 1), 200)
    
    # Filter to last 30 days to ensure we have data for the full frequency chart range
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
        .where(Event.timestamp >= thirty_days_ago)
        .order_by(Event.timestamp.desc())
        .limit(clamped_limit)
    )
    rows = db.execute(q).scalars().all()
    # Lightweight list; frontend can fetch full payload via event endpoint below.
    return [
        {
            "id": str(r.id),
            "timestamp": r.timestamp,
            "level": r.level,
            "message": r.message,
            "environment": r.environment,
            "release": r.release,
        }
        for r in rows
    ]


@router.get("/api/user/projects/{project_id}/events/{event_id}", response_model=dict)
def user_get_event(
    project_id: int,
    event_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    _require_owned_project(db, user=user, project_id=project_id)
    row = db.get(Event, event_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": str(row.id),
        "project_id": row.project_id,
        "timestamp": row.timestamp,
        "level": row.level,
        "message": row.message,
        "environment": row.environment,
        "release": row.release,
        "server_name": row.server_name,
        "fingerprint": row.fingerprint,
        "payload": row.payload,
    }


# --- Account Deletion ---


@router.post("/api/user/deletion-request", response_model=DeletionRequestOut)
def user_request_deletion(
    payload: DeletionRequestCreate,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Request account deletion. Admin will review and fulfill."""
    # Check if there's already a pending request
    existing = db.execute(
        select(DeletionRequest)
        .where(DeletionRequest.user_id == user.id)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Deletion request already pending")

    req = DeletionRequest(
        user_id=user.id,
        reason=payload.reason,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    return DeletionRequestOut(
        id=req.id,
        user_id=req.user_id,
        reason=req.reason,
        created_at=req.created_at,
        fulfilled_at=req.fulfilled_at,
        cancelled_at=req.cancelled_at,
    )


@router.get("/api/user/deletion-request", response_model=DeletionRequestOut | None)
def user_get_deletion_request(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get the current pending deletion request, if any."""
    req = db.execute(
        select(DeletionRequest)
        .where(DeletionRequest.user_id == user.id)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
        .order_by(DeletionRequest.id.desc())
    ).scalars().first()
    if req is None:
        return None
    return DeletionRequestOut(
        id=req.id,
        user_id=req.user_id,
        reason=req.reason,
        created_at=req.created_at,
        fulfilled_at=req.fulfilled_at,
        cancelled_at=req.cancelled_at,
    )


@router.delete("/api/user/deletion-request")
def user_cancel_deletion_request(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending deletion request."""
    req = db.execute(
        select(DeletionRequest)
        .where(DeletionRequest.user_id == user.id)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
        .order_by(DeletionRequest.id.desc())
    ).scalars().first()
    if req is None:
        raise HTTPException(status_code=404, detail="No pending deletion request")
    req.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"ok": True}

