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


def test_wordpress_paths_are_blocked(app_with_web):
    client = app_with_web
    # Test various WordPress paths
    assert client.get("/wp-admin").status_code == 404
    assert client.get("/wp-admin/").status_code == 404
    assert client.get("/wp-content").status_code == 404
    assert client.get("/wp/").status_code == 404
    assert client.get("/wordpress").status_code == 404
    assert client.get("/wordpress/admin").status_code == 404
    assert client.get("/index.php").status_code == 404
    assert client.get("/index.php/").status_code == 404


def test_spa_fallback_with_empty_path(tmp_path, monkeypatch):
    """Test catch-all handler with empty path to cover line 60.
    
    Line 60 checks if normalized_path == "/". This happens when
    the path parameter is empty string, which normalizes to "/".
    We test this by directly calling the route handler function.
    """
    from xrayradar_server.routers.web import register_web
    from fastapi import FastAPI
    from starlette.requests import Request
    
    web_dist = tmp_path / "dist"
    web_dist.mkdir()
    (web_dist / "index.html").write_text("<html>ok</html>")
    monkeypatch.setenv("XRAYRADAR_WEB_DIST", str(web_dist))
    
    # Reset registered apps to allow fresh registration
    import xrayradar_server.routers.web as webmod
    original_apps = webmod._registered_apps.copy()
    webmod._registered_apps.clear()
    
    try:
        app = FastAPI()
        # Register web with catch-all
        register_web(app, register_catch_all=True)
        
        # Find the catch-all route handler
        handler_func = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/{path:path}":
                handler_func = route.endpoint
                break
        
        # Test the handler directly with an empty path string
        # This will normalize to "/" and hit line 60
        if handler_func:
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [],
            }
            request = Request(scope)
            
            # Call handler with empty string - normalizes to "/" in the function
            # This covers line 60: if normalized_path == "/": return True
            import inspect
            if inspect.iscoroutinefunction(handler_func):
                import asyncio
                response = asyncio.run(handler_func(path="", request=request))
            else:
                response = handler_func(path="", request=request)
            
            # Verify it returns the index file
            assert hasattr(response, 'path') or response.status_code == 200
        
        # Also verify normal operation
        client = TestClient(app)
        r = client.get("/")
        assert r.status_code == 200
    finally:
        # Restore original state
        webmod._registered_apps = original_apps
