#!/usr/bin/env python3
"""
Send a real error event with actual exception and stack trace to xrayradar-server.

This script simulates a real application error by:
- Throwing actual exceptions with proper stack traces
- Including breadcrumbs (user activity timeline)
- Including user context
- Including device/runtime information

Usage:
  python scripts/send_real_error.py \
    --base-url http://127.0.0.1:8001 \
    --project-id 1 \
    --token "<token>"
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_stack_frames(exc: Exception) -> list[dict[str, Any]]:
    """Extract stack frames from exception traceback"""
    frames = []
    tb = exc.__traceback__
    
    while tb:
        frame = tb.tb_frame
        f_code = frame.f_code
        
        # Get source context
        context_line = None
        pre_context = []
        post_context = []
        
        try:
            filename = f_code.co_filename
            lineno = tb.tb_lineno
            
            # Try to read source file
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                idx = lineno - 1
                if 0 <= idx < len(lines):
                    context_line = lines[idx].rstrip()
                    # Get 5 lines before
                    pre_start = max(0, idx - 5)
                    pre_context = [line.rstrip() for line in lines[pre_start:idx]]
                    # Get 2 lines after
                    post_context = [line.rstrip() for line in lines[idx + 1:idx + 3]]
            except (IOError, OSError, UnicodeDecodeError, FileNotFoundError):
                pass
        
        except Exception:
            pass
        
        # Determine if in-app code
        filename = f_code.co_filename
        in_app = not any(
            filename.startswith(path)
            for path in [
                "site-packages",
                "python3.",
                "python2.",
                "/usr/lib/python",
                "/usr/local/lib/python",
            ]
        )
        
        frames.append({
            "filename": filename,
            "function": f_code.co_name,
            "lineno": tb.tb_lineno,
            "abs_path": filename,
            "context_line": context_line,
            "pre_context": pre_context,
            "post_context": post_context,
            "in_app": in_app,
        })
        
        tb = tb.tb_next
    
    frames.reverse()  # Reverse to show call order (oldest first)
    return frames


def simulate_application_error() -> Exception:
    """Simulate a real application error with nested function calls"""
    
    def process_user_data(user_id: int, data: dict) -> dict:
        """Simulate processing user data"""
        # Breadcrumb: User action
        breadcrumbs.append({
            "timestamp": _utc_iso(),
            "type": "user",
            "message": f"Processing data for user {user_id}",
            "category": "user.action",
            "data": {"user_id": user_id},
        })
        
        # Simulate a nested call that will fail
        return validate_and_transform(data)
    
    def validate_and_transform(data: dict) -> dict:
        """Simulate validation that fails"""
        # Breadcrumb: Validation step
        breadcrumbs.append({
            "timestamp": _utc_iso(),
            "type": "default",
            "message": "Validating user input",
            "category": "validation",
            "data": {"keys": list(data.keys())},
        })
        
        # This will raise a KeyError
        return {
            "processed": True,
            "value": data["missing_key"],  # This will fail!
        }
    
    # Simulate breadcrumbs leading up to the error
    breadcrumbs.append({
        "timestamp": _utc_iso(),
        "type": "navigation",
        "message": "User navigated to /api/process",
        "category": "navigation",
    })
    
    breadcrumbs.append({
        "timestamp": _utc_iso(),
        "type": "http",
        "message": "POST /api/process",
        "category": "http",
        "data": {"method": "POST", "url": "/api/process"},
    })
    
    # Trigger the error
    try:
        user_data = {"name": "John", "age": 30}
        result = process_user_data(user_id=123, data=user_data)
        return None  # Should not reach here
    except KeyError as e:
        return e


def main() -> int:
    p = argparse.ArgumentParser(description="Send a real error event with exception to xrayradar-server.")
    p.add_argument("--base-url", default="http://127.0.0.1:8001", help="Server base URL.")
    p.add_argument("--project-id", type=int, required=True, help="Project id (e.g. 1).")
    p.add_argument("--token", required=True, help="Token value for X-Xrayradar-Token header.")
    p.add_argument("--environment", default="development", help="contexts.environment value.")
    p.add_argument("--release", default="1.0.0", help="contexts.release value.")
    args = p.parse_args()

    base_url = (args.base_url or "").rstrip("/")
    url = f"{base_url}/api/{args.project_id}/store/"

    # Global breadcrumbs list (simulated)
    global breadcrumbs
    breadcrumbs = []

    # Simulate a real error
    exc = simulate_application_error()
    if exc is None:
        print("Error: No exception was raised", file=sys.stderr)
        return 1

    # Extract stack frames
    frames = _get_stack_frames(exc)

    # Build exception payload
    exception_payload = {
        "values": [{
            "type": type(exc).__name__,
            "value": str(exc),
            "module": exc.__class__.__module__ if exc.__class__.__module__ != "builtins" else None,
            "stacktrace": {
                "frames": frames
            }
        }]
    }

    # Build full event payload
    payload = {
        "timestamp": _utc_iso(),
        "level": "error",
        "message": f"{type(exc).__name__}: {str(exc)}",
        "contexts": {
            "environment": args.environment,
            "release": args.release,
            "server_name": "test-server",
            "runtime": {
                "name": "python",
                "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            },
            "os": {
                "name": sys.platform,
            },
        },
        "user": {
            "id": "123",
            "username": "testuser",
            "email": "testuser@example.com",
            "ip_address": "127.0.0.1",
        },
        "tags": {
            "error_type": type(exc).__name__,
            "component": "data_processing",
            "severity": "high",
        },
        "exception": exception_payload,
        "breadcrumbs": breadcrumbs,
        "platform": "python",
        "sdk": {
            "name": "xrayradar",
            "version": "0.2.0",
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
            print(f"✓ HTTP {resp.status}")
            print(f"✓ Event sent successfully")
            print(f"  Response: {body}")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"✗ HTTP {e.code}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"✗ Request failed: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
