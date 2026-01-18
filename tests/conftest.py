import os

import pytest


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


@pytest.fixture(scope="session")
def database_url(tmp_path_factory) -> str:
    # Always force a throwaway sqlite DB so tests never hit a real database
    # (e.g. Postgres from a dev shell or .env).
    db_dir = tmp_path_factory.mktemp("xrayradar_db")
    db_path = db_dir / "test.sqlite3"
    url = f"sqlite:///{db_path}"
    os.environ["XRAYRADAR_DATABASE_URL"] = url
    return url


@pytest.fixture(autouse=True)
def _dispose_db_engine():
    yield
    try:
        import xrayradar_server.db as dbmod

        dbmod.engine.dispose()
    except Exception:
        pass
