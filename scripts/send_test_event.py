#!/usr/bin/env python3
"""
Send a test event to an XrayRadar server ingestion endpoint.

Usage:
  python scripts/send_test_event.py \
    --base-url http://127.0.0.1:8001 \
    --project-id 1 \
    --token "<token>"
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    p = argparse.ArgumentParser(description="Send a test error event to an XrayRadar server.")
    p.add_argument("--base-url", default="http://127.0.0.1:8001", help="Server base URL.")
    p.add_argument("--project-id", type=int, required=True, help="Project id (e.g. 1).")
    p.add_argument("--token", required=True, help="Token value for X-Xrayradar-Token header.")
    p.add_argument("--message", default="Test error from send_test_event.py", help="Event message.")
    p.add_argument("--environment", default="development", help="contexts.environment value.")
    p.add_argument("--release", default="dev", help="contexts.release value.")
    p.add_argument("--level", default="error", help="Event level (error/warning/info/debug).")
    args = p.parse_args()

    base_url = (args.base_url or "").rstrip("/")
    url = f"{base_url}/api/{args.project_id}/store/"

    try:
        tb = "".join(traceback.format_stack(limit=8))
    except Exception:
        tb = ""

    payload = {
        "timestamp": _utc_iso(),
        "level": args.level,
        "message": args.message,
        "contexts": {
            "environment": args.environment,
            "release": args.release,
            "server_name": "local-dev",
        },
        "exception": {
            "type": "TestError",
            "value": args.message,
            "stacktrace": tb,
        },
        "extra": {
            "sent_by": "scripts/send_test_event.py",
        },
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
            print(f"HTTP {resp.status}")
            print(body)
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"HTTP {e.code}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

