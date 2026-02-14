"""Shared helpers for user API routers."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fastapi import HTTPException

from ...models import Project, ProjectMember, ProjectMemberEnvironment, Token, User


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


def get_allowed_environments(
    db: Session,
    *,
    user: User,
    project_id: int,
) -> set[str] | None:
    """Return allowed environments for this user in the project.

    Returns:
      - None: unrestricted (owner or member without restrictions)
      - set[str]: restricted to those environments
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_user_id == user.id:
        return None

    member = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    ).scalars().first()
    if member is None:
        raise HTTPException(status_code=404, detail="Project not found")

    env_rows = (
        db.execute(
            select(ProjectMemberEnvironment.environment).where(
                ProjectMemberEnvironment.project_id == project_id,
                ProjectMemberEnvironment.user_id == user.id,
            )
        )
        .scalars()
        .all()
    )
    if not env_rows:
        return None
    return {e for e in env_rows if e}


def validate_requested_environments(
    allowed_envs: set[str] | None,
    requested_envs: set[str],
) -> None:
    """Validate requested envs against allowed envs."""
    if allowed_envs is None or not requested_envs:
        return
    if not requested_envs.issubset(allowed_envs):
        raise HTTPException(status_code=404, detail="Project not found")
