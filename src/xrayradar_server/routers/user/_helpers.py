"""Shared helpers for user API routers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException

from ...db import get_db
from ...models import Project, Token, User


def require_owned_project(db: Session, *, user: User, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


def require_user_token(db: Session, *, user: User, token_id: int) -> Token:
    row = db.get(Token, token_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Token not found")
    if row.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Token revoked")
    return row


def user_owned_project_ids_subq(user_id: int):
    """Subquery returning project IDs owned by the user."""
    return select(Project.id).where(Project.owner_user_id == user_id)
