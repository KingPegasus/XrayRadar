import importlib
import os
import sys
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeSerializer
from sqlalchemy import select

# Set a default test database URL before any imports that might use db.py
# This allows imports to succeed even before pytest fixtures run
if "XRAYRADAR_DATABASE_URL" not in os.environ:
    # Use a temporary in-memory SQLite database as default for imports
    # The actual test database will be set by the database_url fixture
    os.environ["XRAYRADAR_DATABASE_URL"] = "sqlite:///:memory:"


def _maybe_parse_env_assignment(raw_line: str) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if not key:
        return None
    return key, value


def _load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                parsed = _maybe_parse_env_assignment(raw_line)
                if parsed is None:
                    continue
                key, value = parsed
                if key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


@pytest.fixture(scope="session", autouse=True)
def database_url(tmp_path_factory) -> str:
    # Always force a throwaway sqlite DB so tests never hit a real database
    # (e.g. Postgres from a dev shell or .env).
    # This fixture is autouse=True so it runs before any tests
    db_dir = tmp_path_factory.mktemp("xrayradar_db")
    db_path = db_dir / "test.sqlite3"
    url = f"sqlite:///{db_path}"
    os.environ["XRAYRADAR_DATABASE_URL"] = url
    # Force engine recreation if it was already initialized with a different URL
    try:
        import xrayradar_server.db as dbmod
        if hasattr(dbmod, "_engine") and dbmod._engine is not None:
            dbmod._engine.dispose()
            dbmod._engine = None
            dbmod._SessionLocal = None
            dbmod._engine_url = None
    except Exception:
        pass
    return url


@pytest.fixture(autouse=True)
def _dispose_db_engine():
    yield
    try:
        import xrayradar_server.db as dbmod

        dbmod.engine.dispose()
    except Exception:
        pass


def _make_session_cookie(*, secret: str, email: str) -> str:
    s = URLSafeSerializer(secret_key=secret, salt="xrayradar-session")
    return s.dumps({"email": email.strip().lower(), "ts": int(datetime.now(timezone.utc).timestamp())})


def _set_user_session(client: TestClient, *, secret: str, email: str) -> None:
    cookie = _make_session_cookie(secret=secret, email=email)
    client.cookies.set("xrayradar_user_session", cookie, domain="localhost", path="/")


@pytest.fixture()
def app_and_client_with_user(database_url, monkeypatch, request):
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

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
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))

    r = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    user_data = r.json()

    db = dbmod.SessionLocal()
    try:
        u = db.execute(select(models.User).where(models.User.email == user_data["email"])).scalars().first()
        if u:
            u.email_verified = True
            db.add(u)
            db.commit()
    finally:
        db.close()

    return mainmod, client, {"email": user_data["email"], "id": user_data["id"]}


@pytest.fixture()
def app_and_client_with_unverified_user(database_url, monkeypatch, request):
    """Same as app_and_client_with_user but leaves email_verified=False."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    monkeypatch.setenv("XRAYRADAR_SESSION_SECRET", "secret")

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
        db.commit()
    finally:
        db.close()

    import xrayradar_server.main as mainmod

    importlib.reload(mainmod)
    client = TestClient(mainmod.app)
    client.__enter__()
    request.addfinalizer(lambda: client.__exit__(None, None, None))

    r = client.post(
        "/auth/signup",
        json={"email": "unverified@example.com", "password": "password123", "plan": "Free"},
    )
    assert r.status_code == 200
    user_data = r.json()
    return mainmod, client, {"email": user_data["email"], "id": user_data["id"]}
