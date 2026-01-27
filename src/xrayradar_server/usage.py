"""Usage tracking and limit enforcement for event storage."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .constants import TIER_EVENT_LIMITS, TIER_WARNING_THRESHOLD
from .models import Event, Project, User


def get_user_event_count(db: Session, user_id: int) -> int:
    """Get the total count of events stored for a user across all their projects."""
    # Count all events in all projects owned by this user
    q = (
        select(func.count(Event.id))
        .join(Project, Event.project_id == Project.id)
        .where(Project.owner_user_id == user_id)
    )
    result = db.execute(q).scalar()
    return result or 0


def get_user_event_limit(user: User) -> int | None:
    """Get the event storage limit for a user based on their plan tier."""
    return TIER_EVENT_LIMITS.get(user.plan)


def check_user_event_limit(
    db: Session, user: User, raise_on_exceed: bool = True
) -> tuple[int, int | None, bool]:
    """
    Check if user has exceeded their event storage limit.

    Returns:
        Tuple of (current_count, limit, is_exceeded)
        If raise_on_exceed is True, raises HTTPException when limit is exceeded.
    """
    current_count = get_user_event_count(db, user.id)
    limit = get_user_event_limit(user)

    if limit is None:
        # Unlimited plan
        is_exceeded = False
    else:
        is_exceeded = current_count >= limit

    if raise_on_exceed and is_exceeded:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Event storage limit exceeded. Current: {current_count}, Limit: {limit}. "
            f"Please upgrade your plan to store more events.",
        )

    return current_count, limit, is_exceeded


def is_near_limit(current_count: int, limit: int | None) -> bool:
    """Check if user is approaching their limit (within warning threshold)."""
    if limit is None:
        return False
    threshold = int(limit * TIER_WARNING_THRESHOLD)
    return current_count >= threshold


def get_user_from_project(db: Session, project: Project) -> User | None:
    """Get the user who owns a project, if any."""
    if project.owner_user_id is None:
        return None
    return db.get(User, project.owner_user_id)
