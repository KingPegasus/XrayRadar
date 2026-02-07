from datetime import datetime, timezone
from uuid import UUID
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_admin
from ..models import DeletionRequest, EmailLog, Event, Project, Token, TokenProjectAccess, TokenRequest, User
from ..schemas import (
    AdminDeletionRequestOut,
    AdminEventListItemOut,
    AdminEventOut,
    AdminStatsOut,
    AdminTokenRequestOut,
    AdminUserOut,
    AdminUserPlanUpdate,
    ProjectOut,
    TokenCreate,
    TokenCreateOut,
    TokenOut,
    TokenProjectAccessOut,
)
from ..usage import get_user_event_count

router = APIRouter()


@router.post("/api/admin/tokens", response_model=TokenCreateOut)
def admin_create_token(
    payload: TokenCreate,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    token_value = secrets.token_urlsafe(32)
    row = Token(
        name=payload.name,
        email=(payload.email or "").strip().lower() or None,
        token=token_value,
        is_admin=payload.is_admin,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TokenCreateOut(
        id=row.id,
        name=row.name,
        email=row.email,
        is_admin=row.is_admin,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
        token=row.token,
    )


@router.get("/api/admin/tokens", response_model=list[TokenOut])
def admin_list_tokens(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    q = select(Token).order_by(Token.id.asc())
    rows = db.execute(q).scalars().all()
    return [
        TokenOut(
            id=r.id,
            name=r.name,
            email=r.email,
            is_admin=r.is_admin,
            created_at=r.created_at,
            revoked_at=r.revoked_at,
        )
        for r in rows
    ]


@router.post("/api/admin/tokens/{token_id}/revoke", response_model=TokenOut)
def admin_revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    row = db.get(Token, token_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
    return TokenOut(
        id=row.id,
        name=row.name,
        email=row.email,
        is_admin=row.is_admin,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
    )


@router.get("/api/admin/projects", response_model=list[ProjectOut])
def admin_list_projects(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    q = select(Project).order_by(Project.id.asc())
    rows = db.execute(q).scalars().all()
    return [ProjectOut(id=p.id, name=p.name) for p in rows]


@router.post(
    "/api/admin/tokens/{token_id}/projects/{project_id}/grant",
    response_model=TokenProjectAccessOut,
)
def admin_grant_project_access(
    token_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    token_row = db.get(Token, token_id)
    if token_row is None:
        raise HTTPException(status_code=404, detail="Token not found")
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

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
    db.refresh(access)
    return TokenProjectAccessOut(
        id=access.id,
        token_id=access.token_id,
        project_id=access.project_id,
        created_at=access.created_at,
        revoked_at=access.revoked_at,
    )


@router.post(
    "/api/admin/tokens/{token_id}/projects/{project_id}/revoke",
    response_model=TokenProjectAccessOut,
)
def admin_revoke_project_access(
    token_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
        .where(TokenProjectAccess.project_id == project_id)
        .where(TokenProjectAccess.revoked_at.is_(None))
        .order_by(TokenProjectAccess.id.desc())
    )
    access = db.execute(q).scalars().first()
    if access is None:
        raise HTTPException(status_code=404, detail="Access not found")

    access.revoked_at = datetime.now(timezone.utc)
    db.add(access)
    db.commit()
    db.refresh(access)
    return TokenProjectAccessOut(
        id=access.id,
        token_id=access.token_id,
        project_id=access.project_id,
        created_at=access.created_at,
        revoked_at=access.revoked_at,
    )


@router.get(
    "/api/admin/tokens/{token_id}/projects",
    response_model=list[TokenProjectAccessOut],
)
def admin_list_token_projects(
    token_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
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


@router.get(
    "/api/admin/projects/{project_id}/events",
    response_model=list[AdminEventListItemOut],
)
def admin_list_project_events(
    project_id: int,
    limit: int = 50,
    before: datetime | None = None,
    level: str | None = None,
    environment: str | None = None,
    release: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

    clamped_limit = min(max(limit, 1), 200)

    dt_before: datetime | None = None
    if before is not None:
        dt_before = before.replace(tzinfo=None) if before.tzinfo else before

    query = select(Event).where(Event.project_id == project_id)
    if dt_before is not None:
        query = query.where(Event.timestamp < dt_before)
    if level:
        query = query.where(Event.level == level)
    if environment:
        query = query.where(Event.environment == environment)
    if release:
        query = query.where(Event.release == release)
    if q and q.strip():
        query = query.where(Event.message.ilike(f"%{q.strip()}%"))

    query = query.order_by(Event.timestamp.desc()).limit(clamped_limit)
    rows = db.execute(query).scalars().all()
    return [
        AdminEventListItemOut(
            id=r.id,
            project_id=r.project_id,
            timestamp=r.timestamp,
            level=r.level,
            message=r.message,
            environment=r.environment,
            release=r.release,
            server_name=r.server_name,
        )
        for r in rows
    ]


@router.get(
    "/api/admin/projects/{project_id}/events/{event_id}",
    response_model=AdminEventOut,
)
def admin_get_project_event(
    project_id: int,
    event_id: UUID,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    row = db.get(Event, event_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Not found")
    return AdminEventOut(
        id=row.id,
        project_id=row.project_id,
        timestamp=row.timestamp,
        level=row.level,
        message=row.message,
        environment=row.environment,
        release=row.release,
        server_name=row.server_name,
        payload=row.payload,
    )


@router.get("/api/admin/token-requests", response_model=list[AdminTokenRequestOut])
def admin_list_token_requests(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    q = select(TokenRequest).order_by(TokenRequest.id.desc())
    rows = db.execute(q).scalars().all()
    # Fetch user emails in one shot
    user_ids = {r.user_id for r in rows}
    users = {}
    if user_ids:
        uq = select(User).where(User.id.in_(sorted(user_ids)))
        users = {u.id: u for u in db.execute(uq).scalars().all()}
    out = []
    for r in rows:
        u = users.get(r.user_id)
        out.append(
            AdminTokenRequestOut(
                id=r.id,
                user_id=r.user_id,
                user_email=(u.email if u else ""),
                name=r.name,
                note=r.note,
                created_at=r.created_at,
                fulfilled_at=r.fulfilled_at,
                fulfilled_token_id=r.fulfilled_token_id,
            )
        )
    return out


@router.post("/api/admin/token-requests/{request_id}/fulfill", response_model=TokenCreateOut)
def admin_fulfill_token_request(
    request_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    req = db.get(TokenRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Token request not found")
    if req.fulfilled_at is not None or req.fulfilled_token_id is not None:
        raise HTTPException(status_code=400, detail="Token request already fulfilled")

    user = db.get(User, req.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    token_value = secrets.token_urlsafe(32)
    row = Token(
        name=req.name,
        email=user.email,
        token=token_value,
        is_admin=False,
        user_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    req.fulfilled_at = datetime.now(timezone.utc)
    req.fulfilled_token_id = row.id
    db.add(req)
    db.commit()

    return TokenCreateOut(
        id=row.id,
        name=row.name,
        email=row.email,
        is_admin=row.is_admin,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
        token=row.token,
    )


@router.get("/api/admin/users", response_model=list[AdminUserOut])
def admin_list_users(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    """List all users with their plan and event count."""
    q = select(User).order_by(User.id.asc())
    rows = db.execute(q).scalars().all()
    out = []
    for u in rows:
        event_count = get_user_event_count(db, u.id)
        out.append(
            AdminUserOut(
                id=u.id,
                email=u.email,
                plan=u.plan,
                created_at=u.created_at,
                event_count=event_count,
            )
        )
    return out


@router.patch("/api/admin/users/{user_id}/plan", response_model=AdminUserOut)
def admin_update_user_plan(
    user_id: int,
    payload: AdminUserPlanUpdate,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    """Update a user's plan (Free, Basic, Pro)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    valid_plans = {"Free", "Basic", "Pro"}
    if payload.plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {', '.join(sorted(valid_plans))}")
    user.plan = payload.plan
    db.add(user)
    db.commit()
    db.refresh(user)
    event_count = get_user_event_count(db, user.id)
    return AdminUserOut(
        id=user.id,
        email=user.email,
        plan=user.plan,
        created_at=user.created_at,
        event_count=event_count,
    )


@router.get("/api/admin/stats", response_model=AdminStatsOut)
def admin_get_stats(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    """Get system statistics for admin dashboard."""
    # Projects count
    projects_total = db.execute(select(func.count(Project.id))).scalar() or 0
    
    # Tokens counts
    tokens_total = db.execute(select(func.count(Token.id))).scalar() or 0
    tokens_active = db.execute(select(func.count(Token.id)).where(Token.revoked_at.is_(None))).scalar() or 0
    tokens_revoked = tokens_total - tokens_active
    
    # Users by plan
    users_free = db.execute(select(func.count(User.id)).where(User.plan == "Free")).scalar() or 0
    users_basic = db.execute(select(func.count(User.id)).where(User.plan == "Basic")).scalar() or 0
    users_pro = db.execute(select(func.count(User.id)).where(User.plan == "Pro")).scalar() or 0
    
    # Events count
    events_total = db.execute(select(func.count(Event.id))).scalar() or 0
    
    # Email counts
    emails_total = db.execute(select(func.count(EmailLog.id)).where(EmailLog.success == True)).scalar() or 0
    emails_verification = db.execute(
        select(func.count(EmailLog.id)).where(
            EmailLog.email_type == "verification",
            EmailLog.success == True
        )
    ).scalar() or 0
    emails_password_reset = db.execute(
        select(func.count(EmailLog.id)).where(
            EmailLog.email_type == "password_reset",
            EmailLog.success == True
        )
    ).scalar() or 0
    emails_error_alert = db.execute(
        select(func.count(EmailLog.id)).where(
            EmailLog.email_type == "error_alert",
            EmailLog.success == True
        )
    ).scalar() or 0
    emails_failed = db.execute(select(func.count(EmailLog.id)).where(EmailLog.success == False)).scalar() or 0
    
    return AdminStatsOut(
        projects_total=projects_total,
        tokens_total=tokens_total,
        tokens_active=tokens_active,
        tokens_revoked=tokens_revoked,
        users_free=users_free,
        users_basic=users_basic,
        users_pro=users_pro,
        events_total=events_total,
        emails_total=emails_total,
        emails_verification=emails_verification,
        emails_password_reset=emails_password_reset,
        emails_error_alert=emails_error_alert,
        emails_failed=emails_failed,
    )


@router.get("/api/admin/deletion-requests", response_model=list[AdminDeletionRequestOut])
def admin_list_deletion_requests(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    """List all pending deletion requests."""
    q = (
        select(DeletionRequest)
        .where(DeletionRequest.fulfilled_at.is_(None))
        .where(DeletionRequest.cancelled_at.is_(None))
        .order_by(DeletionRequest.created_at.desc())
    )
    rows = db.execute(q).scalars().all()
    # Fetch user emails
    user_ids = {r.user_id for r in rows}
    users = {}
    if user_ids:
        uq = select(User).where(User.id.in_(sorted(user_ids)))
        users = {u.id: u for u in db.execute(uq).scalars().all()}
    out = []
    for r in rows:
        u = users.get(r.user_id)
        out.append(
            AdminDeletionRequestOut(
                id=r.id,
                user_id=r.user_id,
                user_email=(u.email if u else ""),
                reason=r.reason,
                created_at=r.created_at,
                fulfilled_at=r.fulfilled_at,
                cancelled_at=r.cancelled_at,
            )
        )
    return out


@router.post("/api/admin/deletion-requests/{request_id}/fulfill")
def admin_fulfill_deletion_request(
    request_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    """Fulfill a deletion request: delete all user data (events, projects, tokens, user)."""
    req = db.get(DeletionRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Deletion request not found")
    if req.fulfilled_at is not None:
        raise HTTPException(status_code=400, detail="Deletion request already fulfilled")
    if req.cancelled_at is not None:
        raise HTTPException(status_code=400, detail="Deletion request was cancelled")

    user = db.get(User, req.user_id)
    if user is None:  # pragma: no cover - edge case if user deleted mid-request
        raise HTTPException(status_code=404, detail="User not found")

    # Delete all events for user's projects
    project_ids = [p.id for p in user.projects]
    if project_ids:
        db.execute(
            Event.__table__.delete().where(Event.project_id.in_(project_ids))
        )

    # Delete user (cascades to projects, tokens, token_requests, deletion_requests)
    db.delete(user)
    db.commit()

    return {"ok": True, "message": f"User {user.email} and all associated data deleted"}
