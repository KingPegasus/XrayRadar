#!/usr/bin/env python3
"""
Console breadcrumb example: capture Python logging as breadcrumbs (type=console).

When capture_as_breadcrumbs=True, log records are added as breadcrumbs instead
of being sent as separate events. When an error is later captured, those
breadcrumbs appear in the event timeline.

Run with your DSN and token, then open the event in the XrayRadar dashboard
to see the console breadcrumbs in the timeline.

Usage:
  python examples/console_breadcrumb_example.py

Set environment variables or edit below:
  XRAYRADAR_DSN=https://your-server.com/your_project_id
  XRAYRADAR_AUTH_TOKEN=your_token
"""

import logging
import os

from xrayradar import ErrorTracker
from xrayradar.integrations.logging import setup_logging

# Use env or replace with your DSN and token
DSN = os.environ.get("XRAYRADAR_DSN", "https://xrayradar.com/your_project_id")
TOKEN = os.environ.get("XRAYRADAR_AUTH_TOKEN", "")

tracker = ErrorTracker(
    dsn=DSN,
    auth_token=TOKEN or None,
    debug=not TOKEN,  # debug=True prints to console if no token
)

# Capture log records as breadcrumbs (type=console), not as separate events
setup_logging(
    client=tracker,
    level=logging.INFO,
    capture_as_breadcrumbs=True,
    exclude_loggers={"urllib3", "requests"},
)

logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("myapp.service")

# These become breadcrumbs (type=console); they will appear in the event timeline
logger.info("User opened settings page")
logger.debug("Cache hit for key user:123:prefs")
logger.info("Loading user preferences")
logger.warning("Deprecated API used: get_legacy_prefs")

# Simulate an error; the event will include the console breadcrumbs above
try:
    raise ValueError("Invalid preference key 'theme'")
except Exception as e:
    tracker.capture_exception(e)
    print("Event sent. Open the event in the dashboard to see console breadcrumbs in the timeline.")
