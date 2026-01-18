import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_with_web(database_url, monkeypatch, tmp_path):
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)

    (dist / "index.html").write_text("<html><body>XRAYRADAR WEB</body></html>", encoding="utf-8")
    (assets / "hello.txt").write_text("hello", encoding="utf-8")

    monkeypatch.setenv("XRAYRADAR_WEB_DIST", str(dist))
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    __import__("xrayradar_server.models")
    dbmod.init_db()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)

    client = TestClient(mainmod.app)
    client.__enter__()
    try:
        yield client
    finally:
        client.__exit__(None, None, None)


def test_root_serves_marketing_site(app_with_web):
    client = app_with_web
    r = client.get("/")
    assert r.status_code == 200
    assert "XRAYRADAR WEB" in r.text


def test_assets_are_served(app_with_web):
    client = app_with_web
    r = client.get("/assets/hello.txt")
    assert r.status_code == 200
    assert r.text == "hello"


def test_spa_fallback_does_not_hijack_api(app_with_web):
    client = app_with_web

    # For an API path, we should hit API routing, not the SPA fallback
    r = client.get("/api/1/events")
    assert r.status_code == 401


def test_spa_fallback_serves_index(app_with_web):
    client = app_with_web
    r = client.get("/pricing")
    assert r.status_code == 200
    assert "XRAYRADAR WEB" in r.text
