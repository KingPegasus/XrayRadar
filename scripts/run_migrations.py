#!/usr/bin/env python3
"""Apply Alembic migrations for Postgres; skip them for SQLite.

SQLite databases are created from the SQLAlchemy models at app startup
(``Base.metadata.create_all`` in ``xrayradar_server.db.init_db``), so the
Postgres-specific Alembic migrations are not needed and would fail on SQLite.
"""

from __future__ import annotations

import os
import subprocess
import sys


def should_run_alembic(database_url: str | None) -> bool:
    """Return True unless the URL targets SQLite."""
    return not (database_url or "").startswith("sqlite")


def main() -> int:
    url = os.getenv("XRAYRADAR_DATABASE_URL")
    if not should_run_alembic(url):
        print(
            "SQLite detected: skipping Alembic migrations "
            "(schema is created by init_db())."
        )
        return 0

    print("Applying Alembic migrations...")
    return subprocess.call(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
