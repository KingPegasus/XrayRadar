"""Tests for user router helpers."""

import pytest

from xrayradar_server.routers.user._helpers import (
    require_owned_project,
    require_project_access,
    require_user_token,
    user_accessible_project_ids_subq,
    user_owned_project_ids_subq,
)
import xrayradar_server.models as models


def test_user_owned_project_ids_subq(app_and_client_with_user):
    """user_owned_project_ids_subq returns a subquery that can be executed."""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        subq = user_owned_project_ids_subq(user["id"])
        result = db.execute(subq)
        ids = [row[0] for row in result.all()]
        # User has no projects yet unless created in another test; subquery is valid
        assert isinstance(ids, list)
    finally:
        db.close()


def test_user_accessible_project_ids_subq_includes_membership(app_and_client_with_user):
    """user_accessible_project_ids_subq returns projects user owns or is a member of."""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        owner = models.User(
            email="owner@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        proj = models.Project(name="P", owner_user_id=owner.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        db.add(models.ProjectMember(project_id=proj.id, user_id=user["id"]))
        db.commit()

        subq = user_accessible_project_ids_subq(user["id"])
        result = db.execute(subq)
        ids = [row[0] for row in result.all()]
        assert proj.id in ids
    finally:
        db.close()


def test_require_project_access_allows_member(app_and_client_with_user):
    """require_project_access returns project when user is member (not owner)."""
    mainmod, client, user = app_and_client_with_user

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        owner = models.User(
            email="owner2@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        proj = models.Project(name="P2", owner_user_id=owner.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        db.add(models.ProjectMember(project_id=proj.id, user_id=user["id"]))
        db.commit()

        user_obj = db.get(models.User, user["id"])
        project = require_project_access(db, user=user_obj, project_id=proj.id)
        assert project.id == proj.id
    finally:
        db.close()


def test_require_owned_project_not_found(app_and_client_with_user):
    """require_owned_project raises 404 when project does not exist."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        user_obj = db.get(models.User, user["id"])
        with pytest.raises(Exception) as exc_info:
            require_owned_project(db, user=user_obj, project_id=99999)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_require_owned_project_not_owner(app_and_client_with_user):
    """require_owned_project raises 404 when project is owned by another user."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other = models.User(
            email="other@example.com",
            password_hash="h",
            plan="Free",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        proj = models.Project(name="OtherProj", owner_user_id=other.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        user_obj = db.get(models.User, user["id"])
        with pytest.raises(Exception) as exc_info:
            require_owned_project(db, user=user_obj, project_id=proj.id)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_require_owned_project_success(app_and_client_with_user):
    """require_owned_project returns project when user owns it."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        proj = models.Project(name="Mine", owner_user_id=user["id"])
        db.add(proj)
        db.commit()
        db.refresh(proj)
        user_obj = db.get(models.User, user["id"])
        project = require_owned_project(db, user=user_obj, project_id=proj.id)
        assert project.id == proj.id
        assert project.owner_user_id == user["id"]
    finally:
        db.close()


def test_require_project_access_not_found(app_and_client_with_user):
    """require_project_access raises 404 when project does not exist."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        user_obj = db.get(models.User, user["id"])
        with pytest.raises(Exception) as exc_info:
            require_project_access(db, user=user_obj, project_id=99999)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_require_project_access_owner(app_and_client_with_user):
    """require_project_access returns project when user is owner."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        proj = models.Project(name="Owned", owner_user_id=user["id"])
        db.add(proj)
        db.commit()
        db.refresh(proj)
        user_obj = db.get(models.User, user["id"])
        project = require_project_access(db, user=user_obj, project_id=proj.id)
        assert project.id == proj.id
    finally:
        db.close()


def test_require_project_access_no_access(app_and_client_with_user):
    """require_project_access raises 404 when user is neither owner nor member."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other = models.User(
            email="other2@example.com",
            password_hash="h",
            plan="Teams",
            email_verified=True,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        proj = models.Project(name="OtherProj2", owner_user_id=other.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        user_obj = db.get(models.User, user["id"])
        with pytest.raises(Exception) as exc_info:
            require_project_access(db, user=user_obj, project_id=proj.id)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_require_user_token_not_found(app_and_client_with_user):
    """require_user_token raises 404 when token does not exist."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        user_obj = db.get(models.User, user["id"])
        with pytest.raises(Exception) as exc_info:
            require_user_token(db, user=user_obj, token_id=99999)
        assert exc_info.value.status_code == 404
    finally:
        db.close()


def test_require_user_token_revoked(app_and_client_with_user):
    """require_user_token raises 400 when token is revoked."""
    mainmod, client, user = app_and_client_with_user
    import xrayradar_server.db as dbmod
    from datetime import datetime, timezone
    db = dbmod.SessionLocal()
    try:
        token = models.Token(
            name="rev",
            token="rev-token",
            user_id=user["id"],
            revoked_at=datetime.now(timezone.utc),
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        user_obj = db.get(models.User, user["id"])
        with pytest.raises(Exception) as exc_info:
            require_user_token(db, user=user_obj, token_id=token.id)
        assert exc_info.value.status_code == 400
    finally:
        db.close()
