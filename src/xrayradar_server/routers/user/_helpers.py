"""Shared helpers for user API routers."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fastapi import HTTPException

from ...models import Project, ProjectMember, Token, User


def require_owned_project(db: Session, *, user: User, project_id: int) -> Project:
    """Require that the user owns the project. Use require_project_access for owner-or-member check."""
    row = db.get(Project, project_id)
    if row is None or row.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


def require_project_access(db: Session, *, user: User, project_id: int) -> Project:
    """Require that the user can access the project (owner or project member)."""
    row = db.get(Project, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if row.owner_user_id == user.id:
        return row
    member = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    ).scalars().first()
    if member is None:
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


def user_accessible_project_ids_subq(user_id: int):
    """Subquery returning project IDs the user can access (owner or project member)."""
    return select(Project.id).where(
        or_(
            Project.owner_user_id == user_id,
            Project.id.in_(select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)),
        )
    )
