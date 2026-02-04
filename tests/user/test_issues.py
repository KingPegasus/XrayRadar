"""Tests for user issues and events endpoints."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from xrayradar_server import models
from xrayradar_server.routers.user.issues import _date_str, _ensure_issue_status

def test_date_str_coverage():
    """_date_str branches: datetime, hasattr isoformat, else with space/T (covers 94, 96, 99)."""
    # datetime -> .date().isoformat()
    assert _date_str(datetime(2025, 1, 15, tzinfo=timezone.utc)) == "2025-01-15"
    # hasattr isoformat (e.g. date)
    assert _date_str(date(2025, 1, 16)) == "2025-01-16"
    # else: str has " " or "T" -> split
    class WithSpace:
        def __str__(self):
            return "2025-01-17 00:00:00"
    assert _date_str(WithSpace()) == "2025-01-17"
    class WithT:
        def __str__(self):
            return "2025-01-18T00:00:00"
    assert _date_str(WithT()) == "2025-01-18"


def test_ensure_issue_status(app_and_client_with_user):
    """Test _ensure_issue_status helper function"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        # Test creating new status when none exists
        status = _ensure_issue_status(db, project_id, "fp-new-status")
        assert status is not None
        assert status.project_id == project_id
        assert status.fingerprint == "fp-new-status"
        assert status.status == "open"
        assert status.reopened is False
        
        # Test returning existing status (should return same object)
        status2 = _ensure_issue_status(db, project_id, "fp-new-status")
        assert status2.project_id == status.project_id
        assert status2.fingerprint == status.fingerprint
        assert status2.status == "open"
        
        # Test with different fingerprint
        status3 = _ensure_issue_status(db, project_id, "fp-another-status")
        assert status3.fingerprint == "fp-another-status"
        assert status3.status == "open"
    finally:
        db.close()


def test_user_list_issues_empty(app_and_client_with_user):
    """Test listing issues when project has none"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/issues")
    assert r.status_code == 200
    assert r.json() == []


def test_user_list_issues_with_events(app_and_client_with_user):
    """Test listing issues with events (covers lines 208-218)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprints
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event1 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 1",
            fingerprint="fp1",
            payload={}
        )
        event2 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 2",
            fingerprint="fp2",
            payload={}
        )
        # Event with same fingerprint
        event3 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 1",
            fingerprint="fp1",
            payload={}
        )
        db.add_all([event1, event2, event3])
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/issues")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2  # Two unique fingerprints
    # Check that counts are correct
    fp1_issue = next((i for i in data if i["fingerprint"] == "fp1"), None)
    assert fp1_issue is not None
    assert fp1_issue["count"] == 2  # Two events with fp1
    assert fp1_issue["first_seen"] is not None
    assert fp1_issue["last_seen"] is not None


def test_user_list_issues_limit_clamping(app_and_client_with_user):
    """Test limit clamping in issues endpoint"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create many events with different fingerprints
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        events = []
        for i in range(15):
            events.append(models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message=f"Test error {i}",
                fingerprint=f"fp{i}",
                payload={}
            ))
        db.add_all(events)
        db.commit()
    finally:
        db.close()

    # Test with limit=0 (should clamp to 1)
    r = client.get(f"/api/user/projects/{project_id}/issues?limit=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1  # Clamped to minimum 1

    # Test with limit=300 (should clamp to 200)
    r = client.get(f"/api/user/projects/{project_id}/issues?limit=300")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 15  # All fingerprints, but limit was clamped to 200


def test_user_list_issues_continue_branch(app_and_client_with_user):
    """Test the continue branch when latest is None (covers line 216-217)
    
    This tests the defensive check where if a fingerprint appears in the aggregation
    but the latest event query returns None, we skip it. We test this by directly
    calling the function with a mocked database session.
    """
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprints
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event1 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error",
            fingerprint="fp1",
            payload={}
        )
        event2 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error 2",
            fingerprint="fp2",
            payload={}
        )
        db.add_all([event1, event2])
        db.commit()
        db.refresh(event1)
        db.refresh(event2)
    finally:
        db.close()

    # Test the function directly with a mocked session
    from xrayradar_server.routers.user.issues import user_list_issues
    from xrayradar_server.models import User

    # Get the actual User model instance
    test_db = dbmod.SessionLocal()
    try:
        user_obj = test_db.get(User, user["id"])
        assert user_obj is not None

        latest_query_count = [0]
        original_execute = test_db.execute

        def mock_execute(statement, *args, **kwargs):
            # Check if this is the latest event query (has limit(1))
            if hasattr(statement, '_limit_clause') and statement._limit_clause is not None:
                # Check if it's filtering by fingerprint
                if hasattr(statement, 'whereclause') and statement.whereclause is not None:
                    latest_query_count[0] += 1
                    if latest_query_count[0] == 2:  # Second query (for fp2)
                        # Return a mock result that yields None
                        mock_result = MagicMock()
                        mock_scalars = MagicMock()
                        mock_scalars.first.return_value = None
                        mock_result.scalars.return_value = mock_scalars
                        return mock_result
            return original_execute(statement, *args, **kwargs)

        test_db.execute = mock_execute

        # Call the function directly
        result = user_list_issues(project_id, limit=50, user=user_obj, db=test_db)
        
        # Should only have fp1 (fp2 was skipped due to continue)
        assert len(result) == 1
        assert result[0].fingerprint == "fp1"
    finally:
        test_db.close()


def test_user_list_issue_events(app_and_client_with_user):
    """Test listing issue events (covers lines 245-255)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprint
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event1 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error",
            fingerprint="abc123",
            payload={}
        )
        event2 = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test error",
            fingerprint="abc123",
            payload={}
        )
        db.add_all([event1, event2])
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/issues/abc123/events")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all(e["level"] == "error" for e in data)
    assert all("id" in e for e in data)


def test_user_list_issue_events_limit_clamping(app_and_client_with_user):
    """Test limit clamping in issue events (covers lines 245-255)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create events with fingerprint
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        events = []
        for i in range(10):
            events.append(models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message=f"Test error {i}",
                fingerprint="abc123",
                payload={}
            ))
        db.add_all(events)
        db.commit()
    finally:
        db.close()

    # Test with limit=0 (should clamp to 1)
    r = client.get(f"/api/user/projects/{project_id}/issues/abc123/events?limit=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1  # Clamped to minimum 1

    # Test with limit=300 (should clamp to 200)
    r = client.get(f"/api/user/projects/{project_id}/issues/abc123/events?limit=300")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 10  # All events, but limit was clamped to 200


def test_user_get_event_success(app_and_client_with_user):
    """Test getting event successfully (covers line 279)"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    # Create event
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        event = models.Event(
            project_id=project_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            level="error",
            message="Test error",
            fingerprint="abc123",
            payload={"test": "data"}
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/events/{event_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(event_id)
    assert data["project_id"] == project_id
    assert data["message"] == "Test error"
    assert data["payload"] == {"test": "data"}


def test_user_list_issues_not_owned(app_and_client_with_user):
    """Test listing issues fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        r = client.get(f"/api/user/projects/{other_project.id}/issues")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_list_issue_events_not_owned(app_and_client_with_user):
    """Test listing issue events fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        r = client.get(f"/api/user/projects/{other_project.id}/issues/abc123/events")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_get_event_not_owned_project(app_and_client_with_user):
    """Test getting event fails for non-owned project"""
    mainmod, client, user = app_and_client_with_user

    # Create another user's project and event
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        other_user = models.User(email="other@example.com", password_hash="hash", plan="Free")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_project = models.Project(name="Other Project", owner_user_id=other_user.id)
        db.add(other_project)
        db.commit()
        db.refresh(other_project)

        event = models.Event(
            project_id=other_project.id,
            timestamp=datetime.now(timezone.utc),
            level="error",
            message="Test",
            fingerprint="abc123",
            payload={}
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        r = client.get(f"/api/user/projects/{other_project.id}/events/{event.id}")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_get_event_not_found(app_and_client_with_user):
    """Test getting non-existent event"""
    mainmod, client, user = app_and_client_with_user

    # Create project
    r1 = client.post("/api/user/projects", json={"name": "My Project"})
    project_id = r1.json()["id"]

    fake_id = uuid4()
    r = client.get(f"/api/user/projects/{project_id}/events/{fake_id}")
    assert r.status_code == 404


def test_user_get_event_wrong_project(app_and_client_with_user):
    """Test getting event from wrong project"""
    mainmod, client, user = app_and_client_with_user

    # Create two projects
    r1 = client.post("/api/user/projects", json={"name": "Project 1"})
    project_id_1 = r1.json()["id"]

    r2 = client.post("/api/user/projects", json={"name": "Project 2"})
    project_id_2 = r2.json()["id"]

    # Create event in project 1
    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        event = models.Event(
            project_id=project_id_1,
            timestamp=datetime.now(timezone.utc),
            level="error",
            message="Test",
            fingerprint="abc123",
            payload={}
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        # Try to get event from project 2
        r = client.get(f"/api/user/projects/{project_id_2}/events/{event.id}")
        assert r.status_code == 404
    finally:
        db.close()


def test_user_list_project_events_empty(app_and_client_with_user):
    """GET project events when none in last 30 days returns empty list."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/events")
    assert r.status_code == 200
    assert r.json() == []


def test_user_get_project_event_frequency_empty(app_and_client_with_user):
    """GET project event frequency when no events returns empty frequency and total 0."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/events/frequency")
    assert r.status_code == 200
    data = r.json()
    assert data["frequency"] == {}
    assert data["total"] == 0


def test_user_list_project_events_and_frequency_with_events(app_and_client_with_user):
    """GET project events and frequency with stored events returns data."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        evt = models.Event(
            project_id=project_id,
            timestamp=datetime.now(timezone.utc) - timedelta(days=1),
            level="error",
            message="test",
            payload={},
            fingerprint="fp1",
        )
        db.add(evt)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/events")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0].get("message") == "test"

    r = client.get(f"/api/user/projects/{project_id}/events/frequency")
    assert r.status_code == 200
    freq = r.json()
    assert freq["total"] >= 1
    assert isinstance(freq["frequency"], dict)
    assert len(freq["frequency"]) >= 1

    r = client.get(f"/api/user/projects/{project_id}/issues/fp1/events")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.get(f"/api/user/projects/{project_id}/issues/fp1/events/frequency")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert isinstance(data["frequency"], dict)


def test_user_get_issue_event_frequency_empty(app_and_client_with_user):
    """GET issue event frequency when no events for fingerprint returns empty."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    r = client.get(f"/api/user/projects/{project_id}/issues/fp123/events/frequency")
    assert r.status_code == 200
    data = r.json()
    assert data["frequency"] == {}
    assert data["total"] == 0


def test_user_get_issue_breakdown(app_and_client_with_user):
    """GET issue breakdown returns event counts by release and by environment."""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    assert r1.status_code == 200
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for release, env, count in [("1.0.0", "production", 2), ("1.0.1", "production", 1), ("1.0.0", "staging", 1)]:
            for _ in range(count):
                e = models.Event(
                    project_id=project_id,
                    timestamp=now,
                    level="error",
                    message="Err",
                    fingerprint="fp-breakdown",
                    environment=env,
                    release=release,
                    payload={},
                )
                db.add(e)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/issues/fp-breakdown/breakdown")
    assert r.status_code == 200
    data = r.json()
    assert "by_release" in data
    assert "by_environment" in data
    by_release = {x["release"]: x["count"] for x in data["by_release"]}
    assert by_release.get("1.0.0") == 3
    assert by_release.get("1.0.1") == 1
    by_env = {x["environment"]: x["count"] for x in data["by_environment"]}
    assert by_env.get("production") == 3
    assert by_env.get("staging") == 1


def test_update_issue_status(app_and_client_with_user):
    """Test updating issue status"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-status",
            payload={},
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    # Update status to resolved with release
    r = client.patch(
        f"/api/user/projects/{project_id}/issues/fp-status/status",
        json={"status": "resolved", "resolved_release": "v1.0.0", "notes": "Fixed"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["resolved_release"] == "v1.0.0"
    assert data["notes"] == "Fixed"
    assert data["resolved_at"] is not None
    assert data["resolved_by_user_id"] == user["id"]
    assert data["reopened"] is False

    # Update status to in_progress
    r = client.patch(
        f"/api/user/projects/{project_id}/issues/fp-status/status",
        json={"status": "in_progress"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "in_progress"
    assert data["resolved_release"] is None
    assert data["resolved_at"] is None


def test_resolve_with_release(app_and_client_with_user):
    """Test resolving issue with release tracking"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-release",
            payload={},
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    r = client.patch(
        f"/api/user/projects/{project_id}/issues/fp-release/status",
        json={"status": "resolved", "resolved_release": "v2.0.0"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["resolved_release"] == "v2.0.0"
    assert data["reopened"] is False

    # Verify in database
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, "fp-release"))
        assert status is not None
        assert status.status == "resolved"
        assert status.resolved_release == "v2.0.0"
        assert status.reopened is False
    finally:
        db.close()


def test_auto_reopen_on_new_release(app_and_client_with_user):
    """Test auto-reopen when issue occurs in different release"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    from xrayradar_server.fingerprinting import compute_fingerprint
    
    # Create an event to get its fingerprint
    test_event = {
        "level": "error",
        "message": "Auto reopen test",
        "contexts": {"release": "v1.0.0"},
    }
    fp = compute_fingerprint(test_event)
    
    db = dbmod.SessionLocal()
    try:
        # Create resolved issue with the computed fingerprint
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint=fp,
            status="resolved",
            resolved_release="v1.0.0",
            resolved_at=datetime.now(timezone.utc).replace(tzinfo=None),
            resolved_by_user_id=user["id"],
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Store event with different release (same message to get same fingerprint)
    import secrets
    import xrayradar_server.db as dbmod
    token_value = secrets.token_urlsafe(32)
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token=token_value, email=None, is_admin=False, user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)
        
        # Grant token access to project
        access = models.TokenProjectAccess(token_id=token.id, project_id=project_id)
        db.add(access)
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/{project_id}/store/",
        json={
            "level": "error",
            "message": "Auto reopen test",
            "contexts": {"release": "v2.0.0"},
        },
        headers={"X-Xrayradar-Token": token_value},
    )
    assert r.status_code == 200

    # Verify issue was auto-reopened
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, fp))
        assert status is not None
        assert status.status == "open"
        assert status.reopened is True
        assert status.resolved_release is None
        assert status.resolved_at is None
    finally:
        db.close()


def test_auto_reopen_same_release_reopens(app_and_client_with_user):
    """Test that resolved issue auto-reopens when event has same release (recurrence indicates fix didn't work)"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    from xrayradar_server.fingerprinting import compute_fingerprint
    
    # Create an event to get its fingerprint
    test_event = {
        "level": "error",
        "message": "Same release test",
        "contexts": {"release": "v1.0.0"},
    }
    fp = compute_fingerprint(test_event)
    
    db = dbmod.SessionLocal()
    try:
        # Create resolved issue with the computed fingerprint
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint=fp,
            status="resolved",
            resolved_release="v1.0.0",
            resolved_at=datetime.now(timezone.utc).replace(tzinfo=None),
            resolved_by_user_id=user["id"],
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Store event with same release (same message to get same fingerprint)
    import secrets
    import xrayradar_server.db as dbmod
    token_value = secrets.token_urlsafe(32)
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token=token_value, email=None, is_admin=False, user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)
        
        # Grant token access to project
        access = models.TokenProjectAccess(token_id=token.id, project_id=project_id)
        db.add(access)
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/{project_id}/store/",
        json={
            "level": "error",
            "message": "Same release test",
            "contexts": {"release": "v1.0.0"},
        },
        headers={"X-Xrayradar-Token": token_value},
    )
    assert r.status_code == 200

    # Verify issue was auto-reopened (recurrence in same release means fix didn't work)
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, fp))
        assert status is not None
        assert status.status == "open"
        assert status.reopened is True
        assert status.resolved_release is None
        assert status.resolved_at is None
    finally:
        db.close()


def test_bulk_update_status(app_and_client_with_user):
    """Test bulk updating multiple issues"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for i, fp in enumerate(["fp-bulk1", "fp-bulk2", "fp-bulk3"]):
            event = models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message=f"Test {i}",
                fingerprint=fp,
                payload={},
            )
            db.add(event)
        db.commit()
    finally:
        db.close()

    r = client.post(
        f"/api/user/projects/{project_id}/issues/bulk-status",
        json={
            "fingerprints": ["fp-bulk1", "fp-bulk2", "fp-bulk3"],
            "status": "resolved",
            "resolved_release": "v1.0.0",
        }
    )
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 3

    # Verify all were updated
    db = dbmod.SessionLocal()
    try:
        for fp in ["fp-bulk1", "fp-bulk2", "fp-bulk3"]:
            status = db.get(models.IssueStatus, (project_id, fp))
            assert status is not None
            assert status.status == "resolved"
            assert status.resolved_release == "v1.0.0"
            assert status.reopened is False
    finally:
        db.close()


def test_list_issues_with_status_filter(app_and_client_with_user):
    """Test filtering issues by status"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Create events with different fingerprints
        for fp in ["fp-open", "fp-resolved", "fp-ignored"]:
            event = models.Event(
                project_id=project_id,
                timestamp=now,
                level="error",
                message="Test",
                fingerprint=fp,
                payload={},
            )
            db.add(event)
        
        # Set statuses
        status1 = models.IssueStatus(project_id=project_id, fingerprint="fp-resolved", status="resolved")
        status2 = models.IssueStatus(project_id=project_id, fingerprint="fp-ignored", status="ignored")
        db.add_all([status1, status2])
        db.commit()
    finally:
        db.close()

    # Filter by resolved
    r = client.get(f"/api/user/projects/{project_id}/issues?status=resolved")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["fingerprint"] == "fp-resolved"
    assert data[0]["status"] == "resolved"

    # Filter by ignored
    r = client.get(f"/api/user/projects/{project_id}/issues?status=ignored")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["fingerprint"] == "fp-ignored"

    # Filter by open (should include fp-open which has no status record)
    r = client.get(f"/api/user/projects/{project_id}/issues?status=open")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["fingerprint"] == "fp-open"


def test_ignored_issue_no_auto_reopen(app_and_client_with_user):
    """Test that ignored issues don't auto-reopen"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    from xrayradar_server.fingerprinting import compute_fingerprint
    
    # Create an event to get its fingerprint
    test_event = {
        "level": "error",
        "message": "Ignored error test",
        "contexts": {"release": "v2.0.0"},
    }
    fp = compute_fingerprint(test_event)
    
    db = dbmod.SessionLocal()
    try:
        # Create ignored issue with the computed fingerprint
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint=fp,
            status="ignored",
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Store event with different release (same message to get same fingerprint)
    import secrets
    import xrayradar_server.db as dbmod
    token_value = secrets.token_urlsafe(32)
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token=token_value, email=None, is_admin=False, user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)
        
        # Grant token access to project
        access = models.TokenProjectAccess(token_id=token.id, project_id=project_id)
        db.add(access)
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/{project_id}/store/",
        json={
            "level": "error",
            "message": "Ignored error test",
            "contexts": {"release": "v2.0.0"},
        },
        headers={"X-Xrayradar-Token": token_value},
    )
    assert r.status_code == 200

    # Verify issue stays ignored (reopened flag should not be set)
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, fp))
        assert status is not None
        assert status.status == "ignored"
        assert status.reopened is False
    finally:
        db.close()


def test_auto_reopen_resolved_without_release(app_and_client_with_user):
    """Test auto-reopen when resolved issue has no release tracking"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    from xrayradar_server.fingerprinting import compute_fingerprint
    
    # Create an event to get its fingerprint
    test_event = {
        "level": "error",
        "message": "No release tracking test",
    }
    fp = compute_fingerprint(test_event)
    
    db = dbmod.SessionLocal()
    try:
        # Create resolved issue without release tracking
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint=fp,
            status="resolved",
            resolved_release=None,  # No release tracking
            resolved_at=datetime.now(timezone.utc).replace(tzinfo=None),
            resolved_by_user_id=user["id"],
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Store new event (same message to get same fingerprint)
    import secrets
    import xrayradar_server.db as dbmod
    token_value = secrets.token_urlsafe(32)
    db = dbmod.SessionLocal()
    try:
        token = models.Token(name="test", token=token_value, email=None, is_admin=False, user_id=user["id"])
        db.add(token)
        db.commit()
        db.refresh(token)
        
        # Grant token access to project
        access = models.TokenProjectAccess(token_id=token.id, project_id=project_id)
        db.add(access)
        db.commit()
    finally:
        db.close()
    r = client.post(
        f"/api/{project_id}/store/",
        json={
            "level": "error",
            "message": "No release tracking test",
        },
        headers={"X-Xrayradar-Token": token_value},
    )
    assert r.status_code == 200

    # Verify issue was auto-reopened (since resolved_release is null)
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, fp))
        assert status is not None
        assert status.status == "open"
        assert status.reopened is True
        assert status.resolved_at is None
    finally:
        db.close()


def test_list_issues_includes_status(app_and_client_with_user):
    """Test that list issues includes status information"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-with-status",
            payload={},
        )
        db.add(event)
        
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint="fp-with-status",
            status="in_progress",
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    r = client.get(f"/api/user/projects/{project_id}/issues")
    assert r.status_code == 200
    data = r.json()
    issue = next((i for i in data if i["fingerprint"] == "fp-with-status"), None)
    assert issue is not None
    assert issue["status"] == "in_progress"
    assert issue.get("reopened") is False
    # Issue without status should default to "open"
    assert all(i.get("status") in ("open", "in_progress", "resolved", "ignored") for i in data)


def test_reopened_flag_cleared_on_resolve(app_and_client_with_user):
    """Test that reopened flag is cleared when resolving an issue"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-reopened-clear",
            payload={},
        )
        db.add(event)
        
        # Create reopened issue
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint="fp-reopened-clear",
            status="open",
            reopened=True,
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Resolve the issue
    r = client.patch(
        f"/api/user/projects/{project_id}/issues/fp-reopened-clear/status",
        json={"status": "resolved", "resolved_release": "v1.0.0"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "resolved"
    assert data["reopened"] is False

    # Verify in database
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, "fp-reopened-clear"))
        assert status is not None
        assert status.status == "resolved"
        assert status.reopened is False
    finally:
        db.close()


def test_update_status_invalid_status(app_and_client_with_user):
    """Test updating issue status with invalid status value"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-invalid",
            payload={},
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    # Try to update with invalid status
    r = client.patch(
        f"/api/user/projects/{project_id}/issues/fp-invalid/status",
        json={"status": "invalid_status"}
    )
    assert r.status_code == 400
    assert "Invalid status" in r.json()["detail"]


def test_manual_reopen_resolved_to_open(app_and_client_with_user):
    """Test manually changing status from resolved to open marks as reopened"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-manual-reopen",
            payload={},
        )
        db.add(event)
        
        # Create resolved issue
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint="fp-manual-reopen",
            status="resolved",
            resolved_release="v1.0.0",
            resolved_at=datetime.now(timezone.utc).replace(tzinfo=None),
            resolved_by_user_id=user["id"],
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Manually change from resolved to open
    r = client.patch(
        f"/api/user/projects/{project_id}/issues/fp-manual-reopen/status",
        json={"status": "open"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "open"
    assert data["reopened"] is True
    assert data["resolved_release"] is None
    assert data["resolved_at"] is None

    # Verify in database
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, "fp-manual-reopen"))
        assert status is not None
        assert status.status == "open"
        assert status.reopened is True
        assert status.resolved_release is None
        assert status.resolved_at is None
    finally:
        db.close()


def test_bulk_update_invalid_status(app_and_client_with_user):
    """Test bulk update with invalid status value"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-bulk-invalid",
            payload={},
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    # Try bulk update with invalid status
    r = client.post(
        f"/api/user/projects/{project_id}/issues/bulk-status",
        json={
            "fingerprints": ["fp-bulk-invalid"],
            "status": "invalid_status"
        }
    )
    assert r.status_code == 400
    assert "Invalid status" in r.json()["detail"]


def test_bulk_update_existing_status_with_notes(app_and_client_with_user):
    """Test bulk update with existing status and notes update"""
    mainmod, client, user = app_and_client_with_user

    r1 = client.post("/api/user/projects", json={"name": "P"})
    project_id = r1.json()["id"]

    import xrayradar_server.db as dbmod
    db = dbmod.SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            project_id=project_id,
            timestamp=now,
            level="error",
            message="Test",
            fingerprint="fp-bulk-existing",
            payload={},
        )
        db.add(event)
        
        # Create existing resolved status
        status = models.IssueStatus(
            project_id=project_id,
            fingerprint="fp-bulk-existing",
            status="resolved",
            resolved_release="v1.0.0",
            resolved_at=datetime.now(timezone.utc).replace(tzinfo=None),
            resolved_by_user_id=user["id"],
        )
        db.add(status)
        db.commit()
    finally:
        db.close()

    # Bulk update existing resolved status to open (should mark as reopened and clear resolution)
    r = client.post(
        f"/api/user/projects/{project_id}/issues/bulk-status",
        json={
            "fingerprints": ["fp-bulk-existing"],
            "status": "open",
            "notes": "Reopened manually"
        }
    )
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 1

    # Verify in database
    db = dbmod.SessionLocal()
    try:
        status = db.get(models.IssueStatus, (project_id, "fp-bulk-existing"))
        assert status is not None
        assert status.status == "open"
        assert status.reopened is True
        assert status.resolved_release is None
        assert status.resolved_at is None
        assert status.resolved_by_user_id is None
        assert status.notes == "Reopened manually"
    finally:
        db.close()

