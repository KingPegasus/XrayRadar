#!/usr/bin/env python3
"""
Send a test event with console-type breadcrumbs to xrayradar-server.

Simulates what the Python SDK sends when using the logging integration
with capture_as_breadcrumbs=True: log records become breadcrumbs with
type="console". Use this to verify console breadcrumbs appear correctly
in the event detail timeline.

Usage:
  python scripts/send_console_breadcrumb.py \
    --base-url http://127.0.0.1:8001 \
    --project-id 1 \
    --token "<token>"
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone


def _utc_iso() -> str:
    """Return current UTC time as ISO string with Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Send a test event with console breadcrumbs to xrayradar-server.",
    )
    p.add_argument("--base-url", default="http://127.0.0.1:8001", help="Server base URL.")
    p.add_argument("--project-id", type=int, required=True, help="Project id (e.g. 1).")
    p.add_argument("--token", required=True, help="Token value for X-Xrayradar-Token header.")
    args = p.parse_args()

    base_url = (args.base_url or "").rstrip("/")
    url = f"{base_url}/api/{args.project_id}/store/"

    # Simulate console breadcrumbs (as produced by logging integration with capture_as_breadcrumbs=True)
    now = _utc_iso()
    breadcrumbs = [
        {
            "timestamp": now,
            "type": "console",
            "level": "info",
            "message": "User opened settings page",
            "category": "myapp.views",
            "data": {"logger": "myapp.views", "module": "views", "funcName": "settings", "lineno": 42},
        },
        {
            "timestamp": now,
            "type": "console",
            "level": "debug",
            "message": "Cache hit for key user:123:prefs",
            "category": "myapp.cache",
            "data": {"logger": "myapp.cache", "module": "cache", "funcName": "get", "lineno": 18},
        },
        {
            "timestamp": now,
            "type": "console",
            "level": "info",
            "message": "Loading user preferences",
            "category": "myapp.service",
            "data": {"logger": "myapp.service", "module": "service", "funcName": "get_preferences", "lineno": 56},
        },
        {
            "timestamp": now,
            "type": "console",
            "level": "warning",
            "message": "Deprecated API used: get_legacy_prefs",
            "category": "myapp.service",
            "data": {"logger": "myapp.service", "module": "service", "funcName": "get_preferences", "lineno": 60},
        },
    ]

    payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": now,
        "level": "error",
        "message": "ValueError: Invalid preference key 'theme'",
        "contexts": {
            "environment": "development",
            "release": "1.0.0",
            "server_name": "test-server",
        },
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "Invalid preference key 'theme'",
                    "module": None,
                    "stacktrace": {
                        "frames": [
                            {
                                "filename": "service.py",
                                "function": "get_preferences",
                                "lineno": 62,
                                "in_app": True,
                            },
                        ]
                    },
                }
            ]
        },
        "breadcrumbs": breadcrumbs,
        "platform": "python",
        "sdk": {"name": "xrayradar", "version": "0.7.0"},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Xrayradar-Token": args.token,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print("✓ HTTP", resp.status)
            print("✓ Event with console breadcrumbs sent successfully")
            print("  Response:", body)
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print("✗ HTTP", e.code, file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print("✗ Request failed:", e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
