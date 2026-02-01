"""Tests for user deletion-request endpoints."""


def test_user_deletion_request_flow(app_and_client_with_user):
    """Request deletion, get request, cancel request."""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/user/deletion-request")
    assert r.status_code == 200
    assert r.json() is None

    r = client.post(
        "/api/user/deletion-request",
        json={"reason": "No longer needed"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == user["id"]
    assert data["reason"] == "No longer needed"
    assert "id" in data
    assert "created_at" in data

    r = client.get("/api/user/deletion-request")
    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["reason"] == "No longer needed"

    r = client.delete("/api/user/deletion-request")
    assert r.status_code == 200

    r = client.get("/api/user/deletion-request")
    assert r.status_code == 200
    assert r.json() is None


def test_user_deletion_request_duplicate_400(app_and_client_with_user):
    """Second deletion request while one is pending returns 400."""
    mainmod, client, user = app_and_client_with_user

    r = client.post("/api/user/deletion-request", json={})
    assert r.status_code == 200

    r = client.post("/api/user/deletion-request", json={})
    assert r.status_code == 400
    assert "pending" in r.json().get("detail", "").lower()


def test_user_cancel_deletion_request_no_pending_404(app_and_client_with_user):
    """Cancel deletion request when none pending returns 404."""
    mainmod, client, user = app_and_client_with_user

    r = client.get("/api/me")
    assert r.status_code == 200

    r = client.delete("/api/user/deletion-request")
    assert r.status_code == 404
