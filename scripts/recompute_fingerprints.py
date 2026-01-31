#!/usr/bin/env python3
"""
Recompute fingerprints for existing events using the current fingerprinting logic.

This script updates fingerprints for all events in the database to match the
current fingerprinting implementation (which includes stack traces in the fingerprint).

Usage:
  python scripts/recompute_fingerprints.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src directory to path to import xrayradar_server
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select

from xrayradar_server.db import SessionLocal, get_database_url
from xrayradar_server.fingerprinting import compute_fingerprint
from xrayradar_server.models import Event


def main() -> int:
    try:
        database_url = get_database_url()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Please set XRAYRADAR_DATABASE_URL environment variable", file=sys.stderr)
        return 1
    
    # Mask password in URL for display
    display_url = database_url
    if "@" in database_url:
        # Hide password in connection string
        parts = database_url.split("@")
        if "://" in parts[0]:
            auth_part = parts[0].split("://")[1]
            if ":" in auth_part:
                user = auth_part.split(":")[0]
                display_url = database_url.replace(auth_part, f"{user}:***")
    
    print(f"Connecting to database: {display_url}")
    
    db = SessionLocal()
    try:
        # Get all events
        events = db.execute(select(Event)).scalars().all()
        total = len(events)
        print(f"Found {total} events to process")
        
        updated = 0
        errors = 0
        
        for idx, event in enumerate(events, 1):
            try:
                # Recompute fingerprint from payload
                new_fp = compute_fingerprint(event.payload)
                
                # Only update if fingerprint changed
                if event.fingerprint != new_fp:
                    event.fingerprint = new_fp
                    updated += 1
                    
                    if idx % 100 == 0:
                        print(f"Processed {idx}/{total} events ({updated} updated so far)")
                        db.commit()  # Commit in batches
            except Exception as e:
                errors += 1
                print(f"Error processing event {event.id}: {e}", file=sys.stderr)
        
        # Final commit
        db.commit()
        
        print(f"\nCompleted:")
        print(f"  Total events: {total}")
        print(f"  Updated: {updated}")
        print(f"  Errors: {errors}")
        print(f"  Unchanged: {total - updated - errors}")
        
        if updated > 0:
            print(f"\n✓ Successfully updated {updated} event fingerprints")
            print("  Fingerprints now match the current fingerprinting logic")
        
        return 0 if errors == 0 else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
