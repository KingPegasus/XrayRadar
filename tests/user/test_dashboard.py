"""Tests for user dashboard stats endpoint."""

from datetime import datetime, timedelta, timezone

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
