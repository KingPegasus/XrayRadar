from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Event, Project, Token, TokenProjectAccess, TokenRequest, User
from ..deps import require_user
from ..schemas import (
    IssueSummaryOut,
    TokenProjectAccessOut,
    TokenRequestCreate,
    TokenRequestOut,
    UserProjectCreate,
    UserProjectOut,
    UserTokenOut,
)

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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    row = Project(name=payload.name, owner_user_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return UserProjectOut(id=row.id, name=row.name)


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
    user: User = Depends(require_user),
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
    user: User = Depends(require_user),
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
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .where(Event.fingerprint == fingerprint)
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

