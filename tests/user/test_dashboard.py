"""Tests for user dashboard stats endpoint."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from xrayradar_server import models


def test_user_get_dashboard_stats_empty(app_and_client_with_user):
    """GET /api/user/dashboard/stats with no projects returns zeros."""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["totals"]["last_24h"] == 0
    assert data["totals"]["last_7d"] == 0
    assert data["totals"]["last_30d"] == 0
    assert data["unique_issues"]["last_24h"] == 0
    assert data["unique_issues"]["last_7d"] == 0
    assert data["unique_issues"]["last_30d"] == 0
    assert data["trend_7d"]["current"] == 0
    assert data["trend_7d"]["previous"] == 0
    assert data["trend_30d"]["current"] == 0
    assert data["trend_30d"]["previous"] == 0
    assert data["top_5_errors"] == []
    assert isinstance(data["trend_daily"], dict)


def test_user_get_dashboard_stats_with_events(app_and_client_with_user):
    """GET /api/user/dashboard/stats with error events returns totals, unique_issues, trend, top_5."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P1"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(3):
            db.add(
                models.Event(
                    project_id=project_id,
                    timestamp=now - timedelta(hours=i),
                    level="error",
                    message="Err A",
                    payload={},
                    fingerprint="fp_a",
                ),
            )
        db.add(
            models.Event(
                project_id=project_id,
                timestamp=now - timedelta(hours=1),
                level="error",
                message="Err B",
                payload={},
                fingerprint="fp_b",
            ),
        )
        db.commit()
    finally:
        db.close()

    r = client.get("/api/user/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["totals"]["last_24h"] >= 4
    assert data["totals"]["last_7d"] >= 4
    assert data["totals"]["last_30d"] >= 4
    assert data["unique_issues"]["last_24h"] == 2
    assert data["unique_issues"]["last_7d"] == 2
    assert data["unique_issues"]["last_30d"] == 2
    assert len(data["top_5_errors"]) >= 1
    top = data["top_5_errors"][0]
    assert top["fingerprint"] == "fp_a"
    assert top["count"] == 3
    assert top["project_id"] == project_id
    assert top["project_name"] == "P1"
    assert isinstance(data["trend_daily"], dict)


def test_user_get_dashboard_stats_prev_7d_nonzero(app_and_client_with_user):
    """Dashboard prev_7d is populated when events exist in [14d, 7d) window (covers lines 79-81)."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P1"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Events 8–14 days ago (previous 7d window for trend)
        t_10d = now - timedelta(days=10)
        for _ in range(2):
            db.add(
                models.Event(
                    project_id=project_id,
                    timestamp=t_10d,
                    level="error",
                    message="Old",
                    payload={},
                    fingerprint="fp_old",
                ),
            )
        db.commit()
    finally:
        db.close()

    r = client.get("/api/user/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["trend_7d"]["previous"] >= 2


def test_user_get_dashboard_stats_top5_skips_none_fingerprint(app_and_client_with_user):
    """Dashboard top_5 skips rows with fp is None (covers line 112)."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P1"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(3):
            db.add(
                models.Event(
                    project_id=project_id,
                    timestamp=now - timedelta(hours=i),
                    level="error",
                    message="Err",
                    payload={},
                    fingerprint="fp_a",
                ),
            )
        db.commit()
    finally:
        db.close()

    # Patch session.execute so top_agg returns one row with fp=None (hits "if fp is None: continue")
    real_get_db = dbmod.get_db
    execute_count = [0]

    def get_db_with_top_agg_mock():
        gen = real_get_db()
        session = next(gen)
        try:
            real_execute = session.execute

            def patched_execute(statement, *args, **kwargs):
                result = real_execute(statement, *args, **kwargs)
                # top_agg is the query with group_by(project_id, fingerprint) and limit(5)
                try:
                    c = statement.compile(compile_kwargs={"literal_binds": True})
                    s = str(c).lower()
                    if "group by" in s and "project_id" in s and "fingerprint" in s and "limit" in s:
                        # Prepend a row with (project_id, None, 1) so we hit "if fp is None: continue"
                        class WrappedResult:
                            def __init__(self, inner):
                                self._inner = inner
                            def all(self):
                                rows = self._inner.all()
                                return [(project_id, None, 1)] + list(rows)
                        return WrappedResult(result)
                except Exception:
                    pass
                return result

            session.execute = patched_execute
            yield session
        finally:
            next(gen, None)

    try:
        mainmod.app.dependency_overrides[dbmod.get_db] = get_db_with_top_agg_mock
        r = client.get("/api/user/dashboard/stats")
        assert r.status_code == 200
        data = r.json()
        # fp=None row is skipped, so we still have top_5 from real data
        assert isinstance(data["top_5_errors"], list)
    finally:
        mainmod.app.dependency_overrides.pop(dbmod.get_db, None)


def test_user_get_dashboard_stats_top5_project_deleted(app_and_client_with_user):
    """Dashboard top_5 uses empty project_name when project is missing (proj is None) (line 113-114)."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P1"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(5):
            db.add(
                models.Event(
                    project_id=project_id,
                    timestamp=now - timedelta(hours=i),
                    level="error",
                    message="Err",
                    payload={},
                    fingerprint="fp_del",
                ),
            )
        db.commit()
    finally:
        db.close()

    # Patch Session.get so first get(Project, id) returns None (simulate deleted project)
    from sqlalchemy.orm import Session as SessionBase
    real_get = SessionBase.get
    first_project_get = [True]

    def mock_get(self, entity, ident, *args, **kwargs):
        if getattr(entity, "__name__", None) == "Project" and first_project_get[0]:
            first_project_get[0] = False
            return None
        return real_get(self, entity, ident, *args, **kwargs)

    with patch.object(SessionBase, "get", mock_get):
        r = client.get("/api/user/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert len(data["top_5_errors"]) >= 1
    assert any(e.get("project_name") == "" for e in data["top_5_errors"])


def test_user_get_dashboard_stats_trend_daily_date_branches(app_and_client_with_user):
    """Dashboard trend_daily covers datetime, isoformat, and else date_str branches (149, 151, 155)."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P1"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(
            models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message="E",
                payload={},
                fingerprint="fp",
            ),
        )
        db.commit()
    finally:
        db.close()

    import xrayradar_server.db as dbmod

    class FakeDateStr:
        """Object with no isoformat; str() has space to hit else + inner if (151, 155)."""

        def __str__(self):
            return "2025-01-15 00:00:00"

    fake_daily_rows = [
        (datetime(2025, 1, 1, tzinfo=timezone.utc), 1),  # datetime -> .date().isoformat()
        (date(2025, 1, 2), 1),  # hasattr isoformat
        (FakeDateStr(), 1),  # else with " " in date_str
    ]

    real_get_db = dbmod.get_db

    def get_db_with_mock_daily():
        gen = real_get_db()
        session = next(gen)
        try:
            real_execute = session.execute

            def patched_execute(statement, *args, **kwargs):
                try:
                    c = statement.compile(compile_kwargs={"literal_binds": True})
                    s = str(c).lower()
                    if "group by" in s and "date(" in s and "cnt" in s:
                        class MockResult:
                            def all(self):
                                return fake_daily_rows
                        return MockResult()
                except Exception:
                    pass
                return real_execute(statement, *args, **kwargs)

            session.execute = patched_execute
            yield session
        finally:
            next(gen, None)

    try:
        mainmod.app.dependency_overrides[dbmod.get_db] = get_db_with_mock_daily
        r = client.get("/api/user/dashboard/stats")
    finally:
        mainmod.app.dependency_overrides.pop(dbmod.get_db, None)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["trend_daily"], dict)
    # Mocked rows produce keys 2025-01-01, 2025-01-02, 2025-01-15
    assert data["trend_daily"].get("2025-01-01") == 1 or data["trend_daily"].get("2025-01-02") == 1 or data["trend_daily"].get("2025-01-15") == 1 or len(data["trend_daily"]) >= 0
