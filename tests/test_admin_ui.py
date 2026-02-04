"""Tests for admin UI rendering and structure."""

import importlib
import sys

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer


def _make_session_cookie(*, secret: str, email: str) -> str:
    """Create a session cookie value."""
    s = URLSafeSerializer(secret_key=secret, salt="xrayradar-session")
    return s.dumps({"email": email, "ts": 0})


def _set_admin_session(client: TestClient, *, secret: str, email: str) -> None:
    """Set an admin session cookie on the test client."""
    cookie = _make_session_cookie(secret=secret, email=email)
    client.cookies.set("xrayradar_session", cookie)


@pytest.fixture()
def app_and_client(database_url, monkeypatch, request):
    """Create app and test client fixture."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)

    import xrayradar_server.db as dbmod

    importlib.reload(dbmod)

    sys.modules.pop("xrayradar_server.models", None)
    import xrayradar_server.models as models
    dbmod.init_db()

    db = dbmod.SessionLocal()
    try:
        db.query(models.TokenProjectAccess).delete()
        db.query(models.Event).delete()
        if hasattr(models, "AlertCooldown"):
            db.query(models.AlertCooldown).delete()
        if hasattr(models, "ProjectAlertRecipient"):
            db.query(models.ProjectAlertRecipient).delete()
        if hasattr(models, "ProjectAlertSettings"):
            db.query(models.ProjectAlertSettings).delete()
        db.query(models.TokenRequest).delete()
        db.query(models.Token).delete()
        db.query(models.Project).delete()
        if hasattr(models, "DeletionRequest"):
            db.query(models.DeletionRequest).delete()
        db.query(models.User).delete()
        db.commit()

        db.add(models.Token(id=1, name="admin", token="admin", is_admin=True))
        db.add(models.Project(id=1, name="p1"))
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))
    return mainmod, client


def test_admin_ui_html_structure(app_and_client, monkeypatch):
    """Test that admin UI HTML contains all required structural elements."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check HTML structure
    assert "<!doctype html>" in html
    assert "<html lang=\"en\">" in html
    assert "<head>" in html
    assert "<body>" in html

    # Check header
    assert "xrayradar admin" in html
    assert 'id="who"' in html
    assert 'id="refresh"' in html
    assert 'id="logout"' in html

    # Check navigation
    assert 'data-view="tokens"' in html
    assert 'data-view="requests"' in html
    assert 'data-view="users"' in html
    assert 'data-view="deletions"' in html
    assert 'data-view="logs"' in html

    # Check main views
    assert 'id="view_tokens"' in html
    assert 'id="view_requests"' in html
    assert 'id="view_users"' in html
    assert 'id="view_deletions"' in html
    assert 'id="view_logs"' in html

    # Check tokens view elements
    assert 'id="t_name"' in html  # Token name input
    assert 'id="t_email"' in html  # Token email input
    assert 'id="t_admin"' in html  # Admin select
    assert 'id="create"' in html  # Create button
    assert 'id="tokens"' in html  # Tokens table body
    assert 'id="projects"' in html  # Projects select
    assert 'id="grant"' in html  # Grant button
    assert 'id="grants"' in html  # Grants table body

    # Check requests view elements
    assert 'id="req_rows"' in html

    # Check users view elements
    assert 'id="users_rows"' in html

    # Check deletions view elements
    assert 'id="del_rows"' in html

    # Check logs view elements
    assert 'id="logs_project"' in html
    assert 'id="logs_level"' in html
    assert 'id="logs_env"' in html
    assert 'id="logs_release"' in html
    assert 'id="logs_q"' in html
    assert 'id="logs_load"' in html
    assert 'id="logs_more"' in html
    assert 'id="logs_rows"' in html
    assert 'id="logs_modal"' in html


def test_admin_ui_email_substitution(app_and_client, monkeypatch):
    """Test that email is correctly substituted in the template."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "test-admin@example.com")

    _set_admin_session(client, secret="secret", email="test-admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check that email placeholder is replaced
    assert "__EMAIL__" not in html
    assert "test-admin@example.com" in html

    # Check that email appears in the correct location
    assert '<span id="who">test-admin@example.com</span>' in html


def test_admin_ui_css_inclusion(app_and_client, monkeypatch):
    """Test that CSS styles are included in the HTML."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check that CSS is present (not as external link but embedded)
    assert "<style>" in html
    assert "</style>" in html

    # Check for key CSS rules
    assert "background: #0b1220" in html or "background:#0b1220" in html
    assert "color: #e5e7eb" in html or "color:#e5e7eb" in html
    assert ".navItem" in html
    assert ".view" in html
    assert ".hidden" in html
    assert "button.primary" in html
    assert "button.danger" in html
    assert ".modalOverlay" in html


def test_admin_ui_javascript_inclusion(app_and_client, monkeypatch):
    """Test that JavaScript is included in the HTML."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check that JavaScript is present (not as external link but embedded)
    assert "<script>" in html
    assert "</script>" in html

    # Check for key JavaScript functions and state
    assert "const state" in html
    assert "function qs(id)" in html
    assert "function showErr(el, msg)" in html
    assert "async function api(path" in html
    assert "function setView(view)" in html
    assert "function renderTokens()" in html
    assert "function renderUsers()" in html
    assert "function renderTokenRequests()" in html
    assert "function renderDeletionRequests()" in html
    assert "function renderLogsRows()" in html
    assert "async function loadAll()" in html


def test_admin_ui_template_placeholders_replaced(app_and_client, monkeypatch):
    """Test that all template placeholders are replaced."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check that no template placeholders remain
    assert "__EMAIL__" not in html
    assert "__CSS__" not in html
    assert "__JS__" not in html


def test_admin_ui_direct_render_function():
    """Test the render_admin_ui function directly."""
    from xrayradar_server.admin_ui import render_admin_ui

    response = render_admin_ui(email="direct-test@example.com")
    assert response.status_code == 200
    html = response.body.decode("utf-8")

    # Check structure
    assert "<!doctype html>" in html
    assert "direct-test@example.com" in html
    assert "__EMAIL__" not in html
    assert "__CSS__" not in html
    assert "__JS__" not in html

    # Check that CSS and JS are included
    assert "<style>" in html
    assert "<script>" in html
    assert "const state" in html


def test_admin_ui_navigation_items(app_and_client, monkeypatch):
    """Test that all navigation items are present with correct attributes."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check navigation items have required attributes
    nav_items = ["tokens", "requests", "users", "deletions", "logs"]
    for view in nav_items:
        assert f'data-view="{view}"' in html
        assert 'role="link"' in html
        assert 'tabindex="0"' in html

    # Check navigation labels
    assert "Tokens" in html
    assert "Token requests" in html
    assert "Users" in html
    assert "Deletions" in html
    assert "Project logs" in html


def test_admin_ui_forms_present(app_and_client, monkeypatch):
    """Test that all form elements are present."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check token creation form
    assert 'id="t_name"' in html
    assert 'id="t_email"' in html
    assert 'id="t_admin"' in html
    assert 'id="create"' in html

    # Check project access form
    assert 'id="projects"' in html
    assert 'id="grant"' in html

    # Check logs filter form
    assert 'id="logs_project"' in html
    assert 'id="logs_level"' in html
    assert 'id="logs_env"' in html
    assert 'id="logs_release"' in html
    assert 'id="logs_q"' in html


def test_admin_ui_tables_present(app_and_client, monkeypatch):
    """Test that all table elements are present."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check table bodies exist (these are tbody elements)
    assert 'id="tokens"' in html
    assert 'id="grants"' in html
    assert 'id="req_rows"' in html
    assert 'id="users_rows"' in html
    assert 'id="del_rows"' in html
    assert 'id="logs_rows"' in html

    # Check that tables have headers
    assert "<thead>" in html


def test_admin_ui_modal_present(app_and_client, monkeypatch):
    """Test that the logs modal is present."""
    _, client = app_and_client
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")
    monkeypatch.setenv("XRAYRADAR_ADMIN_EMAILS", "admin@example.com")

    _set_admin_session(client, secret="secret", email="admin@example.com")

    r = client.get("/admin")
    assert r.status_code == 200
    html = r.text

    # Check modal structure
    assert 'id="logs_modal"' in html
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'id="logs_modal_close"' in html
    assert 'id="logs_copy"' in html
    assert 'id="logs_payload"' in html
    assert 'id="logs_modal_meta"' in html
