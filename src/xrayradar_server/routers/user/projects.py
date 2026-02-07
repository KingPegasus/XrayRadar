"""User API: projects and usage."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import Project, ProjectMember, User
from ...deps import require_user, require_verified_user
from ...schemas import UsageOut, UserProjectCreate, UserProjectOut
from ...usage import check_user_event_limit, is_near_limit
from ._helpers import user_accessible_project_ids_subq

router = APIRouter()


@router.get("/api/user/projects", response_model=list[UserProjectOut])
def user_list_projects(user: User = Depends(require_user), db: Session = Depends(get_db)):
    accessible = user_accessible_project_ids_subq(user.id)
    q = select(Project).where(Project.id.in_(accessible)).order_by(Project.id.asc())
    rows = db.execute(q).scalars().all()
    return [
        UserProjectOut(id=p.id, name=p.name, is_owner=(p.owner_user_id == user.id))
        for p in rows
    ]


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
    return UserProjectOut(id=row.id, name=row.name, is_owner=True)


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
