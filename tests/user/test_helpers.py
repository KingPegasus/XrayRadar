"""Tests for user router helpers."""

from xrayradar_server.routers.user._helpers import user_owned_project_ids_subq


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
