"""Tests for usage module (event limits and tracking)."""

import uuid
from datetime import datetime, timezone

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from xrayradar_server import models
from xrayradar_server.usage import (
    get_user_event_count,
    get_user_event_limit,
    check_user_event_limit,
    is_near_limit,
    get_user_from_project,
)


@pytest.fixture
def db_session(database_url):
    import xrayradar_server.db as dbmod
    dbmod.init_db()
    db = dbmod.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def user_and_project(db_session):
    """Create a user and a project owned by that user. Unique email per test to avoid UNIQUE constraint."""
    email = f"usage-{uuid.uuid4().hex}@example.com"
    user = models.User(
        email=email,
        password_hash="hash",
        plan="Free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    project = models.Project(name="P", owner_user_id=user.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return user, project


def test_get_user_event_count_empty(db_session, user_and_project):
    """When user has no events, count is 0."""
    user, project = user_and_project
    assert get_user_event_count(db_session, user.id) == 0


def test_get_user_event_count_with_events(db_session, user_and_project):
    """Count includes events from all user's projects."""
    user, project = user_and_project
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for _ in range(3):
        e = models.Event(
            project_id=project.id,
            timestamp=now,
            level="error",
            message="m",
            payload={},
        )
        db_session.add(e)
    db_session.commit()
    assert get_user_event_count(db_session, user.id) == 3


def test_get_user_event_limit_free():
    """Free plan has limit."""
    user = MagicMock(plan="Free")
    assert get_user_event_limit(user) == 5000


def test_get_user_event_limit_basic():
    """Basic plan has limit."""
    user = MagicMock(plan="Basic")
    assert get_user_event_limit(user) == 50000


def test_get_user_event_limit_pro():
    """Pro plan is unlimited."""
    user = MagicMock(plan="Pro")
    assert get_user_event_limit(user) is None


def test_get_user_event_limit_unknown_tier():
    """Unknown plan returns None (unlimited)."""
    user = MagicMock(plan="Unknown")
    assert get_user_event_limit(user) is None


def test_check_user_event_limit_unlimited(db_session, user_and_project):
    """When limit is None, is_exceeded is False."""
    user, _ = user_and_project
    user.plan = "Pro"
    current, limit, is_exceeded = check_user_event_limit(db_session, user, raise_on_exceed=True)
    assert current == 0
    assert limit is None
    assert is_exceeded is False


def test_check_user_event_limit_under_limit(db_session, user_and_project):
    """When under limit, is_exceeded is False."""
    user, _ = user_and_project
    current, limit, is_exceeded = check_user_event_limit(db_session, user, raise_on_exceed=True)
    assert current == 0
    assert limit == 5000
    assert is_exceeded is False


def test_check_user_event_limit_at_limit_raises(db_session, user_and_project):
    """When at limit and raise_on_exceed True, raises HTTPException."""
    user, project = user_and_project
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with patch("xrayradar_server.usage.TIER_EVENT_LIMITS", {"Free": 2}):
        for _ in range(2):
            e = models.Event(
                project_id=project.id,
                timestamp=now,
                level="error",
                message="m",
                payload={},
            )
            db_session.add(e)
        db_session.commit()
        with pytest.raises(HTTPException) as exc_info:
            check_user_event_limit(db_session, user, raise_on_exceed=True)
        assert exc_info.value.status_code == 403
        assert "limit exceeded" in exc_info.value.detail.lower()


def test_check_user_event_limit_at_limit_no_raise(db_session, user_and_project):
    """When at limit and raise_on_exceed False, returns is_exceeded True."""
    user, project = user_and_project
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with patch("xrayradar_server.usage.TIER_EVENT_LIMITS", {"Free": 2}):
        for _ in range(2):
            e = models.Event(
                project_id=project.id,
                timestamp=now,
                level="error",
                message="m",
                payload={},
            )
            db_session.add(e)
        db_session.commit()
        current, limit, is_exceeded = check_user_event_limit(db_session, user, raise_on_exceed=False)
        assert current == 2
        assert limit == 2
        assert is_exceeded is True


def test_is_near_limit_none_limit():
    """When limit is None, returns False."""
    assert is_near_limit(1000, None) is False


def test_is_near_limit_below_threshold():
    """When below 80% of limit, returns False."""
    assert is_near_limit(3000, 5000) is False  # 60%


def test_is_near_limit_at_threshold():
    """When at or above 80% of limit, returns True."""
    assert is_near_limit(4000, 5000) is True   # 80%
    assert is_near_limit(4500, 5000) is True


def test_get_user_from_project_with_owner(db_session, user_and_project):
    """Returns owner when project has owner_user_id."""
    user, project = user_and_project
    owner = get_user_from_project(db_session, project)
    assert owner is not None
    assert owner.id == user.id
    assert owner.email == user.email


def test_get_user_from_project_no_owner(db_session):
    """Returns None when project has no owner."""
    project = models.Project(name="Orphan", owner_user_id=None)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    assert get_user_from_project(db_session, project) is None
