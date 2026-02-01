"""Tests for user issues and events endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from xrayradar_server import models

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

