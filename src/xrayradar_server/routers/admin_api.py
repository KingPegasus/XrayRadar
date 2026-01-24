from datetime import datetime, timezone
from uuid import UUID
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_admin
from ..models import Event, Project, Token, TokenProjectAccess, TokenRequest, User
from ..schemas import (
    AdminEventListItemOut,
    AdminEventOut,
    AdminTokenRequestOut,
    ProjectOut,
    TokenCreate,
    TokenCreateOut,
    TokenOut,
    TokenProjectAccessOut,
)

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
