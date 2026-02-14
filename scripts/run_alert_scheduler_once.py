#!/usr/bin/env python3
"""Run one alert scheduler pass and process pending email jobs."""

from __future__ import annotations

from xrayradar_server.alert_scheduler import run_once


def main() -> None:
    result = run_once()
    print(f"enqueued_jobs={result['enqueued_jobs']}")


if __name__ == "__main__":
    main()

