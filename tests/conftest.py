import os

import pytest

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
