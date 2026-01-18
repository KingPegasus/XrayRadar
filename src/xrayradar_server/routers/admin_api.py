from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_admin
from ..models import Project, Token, TokenProjectAccess
from ..schemas import (
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
