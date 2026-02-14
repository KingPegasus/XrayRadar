"""User API: tokens and token requests."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import Token, TokenProjectAccess, TokenProjectEnvironmentAccess, TokenRequest, User
from ...deps import require_user, require_verified_user
from ...schemas import (
    TokenProjectAccessOut,
    TokenRequestCreate,
    TokenRequestOut,
    UserTokenOut,
)
from ._helpers import require_owned_project, require_user_token

router = APIRouter()


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
    require_user_token(db, user=user, token_id=token_id)
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
    require_owned_project(db, user=user, project_id=project_id)
    require_user_token(db, user=user, token_id=token_id)

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


@router.post(
    "/api/user/tokens/{token_id}/projects/{project_id}/revoke",
    response_model=dict,
)
def user_revoke_project_access(
    token_id: int,
    project_id: int,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    require_user_token(db, user=user, token_id=token_id)

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
    return {"ok": True}


@router.get(
    "/api/user/tokens/{token_id}/projects/{project_id}/environments",
    response_model=list[str],
)
def user_list_token_project_environments(
    token_id: int,
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    require_user_token(db, user=user, token_id=token_id)
    rows = (
        db.execute(
            select(TokenProjectEnvironmentAccess.environment).where(
                TokenProjectEnvironmentAccess.token_id == token_id,
                TokenProjectEnvironmentAccess.project_id == project_id,
            )
        )
        .scalars()
        .all()
    )
    return [r for r in rows if r]


@router.put(
    "/api/user/tokens/{token_id}/projects/{project_id}/environments",
    response_model=dict,
)
def user_replace_token_project_environments(
    token_id: int,
    project_id: int,
    payload: dict,
    user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    require_owned_project(db, user=user, project_id=project_id)
    require_user_token(db, user=user, token_id=token_id)

    envs = payload.get("environments") if isinstance(payload, dict) else None
    envs = envs if isinstance(envs, list) else []
    normalized: list[str] = []
    seen: set[str] = set()
    for e in envs:
        if not isinstance(e, str):
            continue
        s = e.strip()
        if s and s not in seen:
            seen.add(s)
            normalized.append(s)

    existing = (
        db.execute(
            select(TokenProjectEnvironmentAccess).where(
                TokenProjectEnvironmentAccess.token_id == token_id,
                TokenProjectEnvironmentAccess.project_id == project_id,
            )
        )
        .scalars()
        .all()
    )
    for row in existing:
        db.delete(row)
    db.flush()  # apply deletes before inserts to avoid UNIQUE on replace
    for env in normalized:
        db.add(
            TokenProjectEnvironmentAccess(
                token_id=token_id,
                project_id=project_id,
                environment=env,
            )
        )
    db.commit()
    return {"ok": True, "environments": normalized}


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
