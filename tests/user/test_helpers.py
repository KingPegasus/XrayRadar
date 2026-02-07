"""Tests for user router helpers."""

from xrayradar_server.routers.user._helpers import (
    require_project_access,
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
