#!/usr/bin/env python3
"""Copy all data from a Postgres database into a SQLite database.

The SQLite schema is created from the SQLAlchemy models (which already support
both PostgreSQL and SQLite), then every table is copied row by row while
preserving primary keys and foreign-key relationships.

Usage:
  XRAYRADAR_DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/xrayradar \
      python scripts/migrate_postgres_to_sqlite.py --target sqlite:///xrayradar.db

The source URL defaults to ``XRAYRADAR_DATABASE_URL``. The target defaults to
``sqlite:///./xrayradar.db``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make the src package importable when running from a source checkout.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, select  # noqa: E402

BATCH_SIZE = 500


def _mask_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    auth, host = rest.split("@", 1)
    if ":" in auth:
        auth = auth.split(":")[0] + ":***"
    return f"{scheme}://{auth}@{host}"


def migrate(source_url: str, target_url: str) -> dict[str, int]:
    """Copy every table from ``source_url`` to ``target_url`` and return row counts."""
    from xrayradar_server import models  # noqa: F401  (populates metadata)
    from xrayradar_server.db import Base

    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)

    # Create the target schema from the models (cross-dialect safe).
    Base.metadata.create_all(target_engine)

    counts: dict[str, int] = {}
    try:
        with source_engine.connect() as source_conn:
            for table in Base.metadata.sorted_tables:
                result = source_conn.execution_options(stream_results=True).execute(
                    select(table)
                )
                count = 0
                batch: list[dict] = []
                with target_engine.begin() as target_conn:
                    for row in result.mappings():
                        batch.append(dict(row))
                        count += 1
                        if len(batch) >= BATCH_SIZE:
                            target_conn.execute(table.insert(), batch)
                            batch = []
                    if batch:
                        target_conn.execute(table.insert(), batch)
                counts[table.name] = count
    finally:
        source_engine.dispose()
        target_engine.dispose()

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy all data from Postgres into SQLite."
    )
    parser.add_argument(
        "--source",
        default=os.getenv("XRAYRADAR_DATABASE_URL"),
        help="Source database URL (defaults to XRAYRADAR_DATABASE_URL).",
    )
    parser.add_argument(
        "--target",
        default="sqlite:///./xrayradar.db",
        help="Target SQLite URL (default: sqlite:///./xrayradar.db).",
    )
    args = parser.parse_args()

    if not args.source:
        print(
            "Error: no source database URL. Set XRAYRADAR_DATABASE_URL or pass --source.",
            file=sys.stderr,
        )
        return 1

    print(f"Source: {_mask_url(args.source)}")
    print(f"Target: {_mask_url(args.target)}")

    counts = migrate(args.source, args.target)

    total = sum(counts.values())
    print("Migration complete:")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count} row(s)")
    print(f"  total: {total} row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
