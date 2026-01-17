import importlib
import secrets

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_and_client(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)
    dbmod.init_db()

    import xrayradar_server.models as models

    db = dbmod.SessionLocal()
    try:
        admin_token_value = secrets.token_urlsafe(32)
        admin = models.Token(
            name="admin", token=admin_token_value, is_admin=True)
        db.add(admin)

        project = models.Project(name="p1")
        db.add(project)
        db.commit()
        db.refresh(admin)
        db.refresh(project)
        admin_id = admin.id
        project_id = project.id
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)

    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))
    return mainmod, client, admin_token_value, admin_id, project_id


def test_missing_token_is_unauthorized(app_and_client):
    _, client, _, _, _ = app_and_client
    r = client.get("/api/1/events")
    assert r.status_code == 401


def test_project_access_enforced(app_and_client):
    _, client, admin_token, _, project_id = app_and_client

    r = client.post(
        "/api/admin/tokens",
        json={"name": "ingest", "email": "ingest@example.com", "is_admin": False},
        headers={"X-Xrayradar-Token": admin_token},
    )
    assert r.status_code == 200
    ingest = r.json()
    ingest_token = ingest["token"]
    ingest_id = ingest["id"]
    assert ingest["email"] == "ingest@example.com"

    r = client.post(f"/api/{project_id}/store/", json={"message": "hi"},
                    headers={"X-Xrayradar-Token": ingest_token})
    assert r.status_code == 403

    r = client.post(
        f"/api/admin/tokens/{ingest_id}/projects/{project_id}/grant",
        headers={"X-Xrayradar-Token": admin_token},
    )
    assert r.status_code == 200

    r = client.post(f"/api/{project_id}/store/", json={"message": "hi"},
                    headers={"X-Xrayradar-Token": ingest_token})
    assert r.status_code == 200

    event_id = r.json()["id"]

    r = client.get(f"/api/{project_id}/events",
                   headers={"X-Xrayradar-Token": ingest_token})
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.get(f"/api/{project_id}/events/{event_id}",
                   headers={"X-Xrayradar-Token": ingest_token})
    assert r.status_code == 200

    r = client.post(
        f"/api/admin/tokens/{ingest_id}/projects/{project_id}/revoke",
        headers={"X-Xrayradar-Token": admin_token},
    )
    assert r.status_code == 200

    r = client.get(f"/api/{project_id}/events",
                   headers={"X-Xrayradar-Token": ingest_token})
    assert r.status_code == 403


def test_revoked_token_is_unauthorized(app_and_client):
    _, client, admin_token, _, _ = app_and_client

    r = client.post(
        "/api/admin/tokens",
        json={"name": "t1", "email": "t1@example.com", "is_admin": False},
        headers={"X-Xrayradar-Token": admin_token},
    )
    tok = r.json()
    assert tok["email"] == "t1@example.com"

    r = client.post(
        f"/api/admin/tokens/{tok['id']}/revoke", headers={"X-Xrayradar-Token": admin_token})
    assert r.status_code == 200

    r = client.get("/api/1/events",
                   headers={"X-Xrayradar-Token": tok["token"]})
    assert r.status_code == 401


def test_list_tokens_includes_email(app_and_client):
    _, client, admin_token, _, _ = app_and_client

    r = client.post(
        "/api/admin/tokens",
        json={"name": "with-email",
              "email": "with-email@example.com", "is_admin": False},
        headers={"X-Xrayradar-Token": admin_token},
    )
    assert r.status_code == 200

    r = client.get("/api/admin/tokens",
                   headers={"X-Xrayradar-Token": admin_token})
    assert r.status_code == 200
    tokens = r.json()
    assert any(t.get("email") == "with-email@example.com" for t in tokens)
