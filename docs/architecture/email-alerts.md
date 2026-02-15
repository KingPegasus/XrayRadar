# Email alerts for errors

## Overview

When an error-level event is stored and the project has email alerts enabled, recipients are resolved (owner + configured recipients), and a digest email job is queued for delivery. Alerts are subject to cooldown controls to avoid flooding, including optional environment-level overrides.

Alert timing is now evaluated by a periodic in-process scheduler pass in the web app lifecycle, so due digest emails can be queued even if no fresh event arrives exactly when cooldown expires.

## Architecture

```mermaid
sequenceDiagram
  participant Client
  participant API as store_event
  participant Scheduler as in_process_scheduler
  participant DB as Database
  participant Alerts as notifications
  participant Jobs as email_jobs worker
  participant Resend as Resend API

  Client->>API: POST /api/{id}/store/
  API->>DB: Save event, commit
  API->>Alerts: should_send_alert(project, fingerprint, level, environment)
  alt Ingest path allows immediate alert
    API->>DB: enqueue email_jobs (error_alert digest trigger)
  end
  Scheduler->>DB: evaluate due project/env scopes
  alt Due and new qualifying events since last send
    Scheduler->>DB: enqueue email_jobs (error_alert digest trigger)
  end
  Jobs->>DB: pull pending jobs
  Jobs->>DB: build digest window [last_sent, trigger_time]
  Jobs->>Resend: send
  Jobs->>DB: mark sent/retry/failed
  API->>Client: 200 + event id
```

- **Non-blocking and durable:** Ingest enqueues DB jobs; a worker processes jobs with retry/backoff.
- **Digest semantics:** one alert email per cooldown window (per project trigger), addressed to all configured recipients in a single send.
- **Exclusive scopes:** project-level scope only evaluates unclaimed events (no environment, or environments without their own enabled env alert settings). Events in enabled env scopes (for example `development`) are owned by that env scope and excluded from project-level digests.
- **Dedupe:** Ingest and scheduler share a 90-second enqueue debounce per project/environment; a second enqueue within that window is skipped. Empty digests (no issues in the window) are never sent.
- **Logging semantics:** delivery outcomes are still logged per recipient in `email_log` for auditing and admin stats.

## Recipients

- **Project owner** — `User.email` for the user who owns the project (`Project.owner_user_id`).
- **Additional emails** — Stored in `project_alert_recipients`; deduplicated with owner.
- **Environment recipients (optional)** — Stored in `project_alert_environment_recipients` and merged for matching environment.

## Components

- **Trigger:** `store_event` in `src/xrayradar_server/routers/api.py` (enqueue after commit).
- **Logic:** `src/xrayradar_server/notifications.py` — `get_alert_recipients`, `should_send_alert`.
- **Queue/worker:** `src/xrayradar_server/mail_jobs.py` — enqueue + processing + retry.
- **Scheduler:** `src/xrayradar_server/alert_scheduler.py` — periodic due-check evaluator; run in-process from app lifespan (optionally callable via `scripts/run_alert_scheduler_once.py`).
- **Digest aggregation:** `src/xrayradar_server/notifications.py` — `get_last_alert_sent_at`, `get_top_issues_since`.
- **Settings:** Project-level (`project_alert_settings`, `project_alert_recipients`) plus optional env-level (`project_alert_environment_settings`, `project_alert_environment_recipients`).

## UI Data Flow

The settings UI now separates project-wide and environment-specific alert configuration and persists both in a single PATCH payload:

```mermaid
flowchart LR
    subgraph API
        GET["GET alert-settings"]
        PATCH["PATCH alert-settings"]
    end
    subgraph UI
        ProjectWide["Project-wide section"]
        EnvSections["Environment sections"]
    end
    GET -->|enabled, cooldown, additional_emails, environment_settings| ProjectWide
    GET -->|environment_settings| EnvSections
    ProjectWide -->|enabled, cooldown, additional_emails| PATCH
    EnvSections -->|environment_settings| PATCH
```

## Plan limits

- **Free:** No email alerts. `get_alert_recipients` returns no one for projects owned by a Free user; GET alert-settings returns `enabled=False`, `min_cooldown_minutes=None`; PATCH with `enabled=True` returns 400.
- **Basic:** Email alerts allowed (project-level only); minimum cooldown **10 minutes**. Environment-specific alert settings are not available.
- **Teams / Teams Pro:** Email alerts allowed; minimum cooldown **1 minute**. Environment-specific alert settings (env-level enabled, cooldown, recipients) are available; only these plans can access or configure `environment_settings` in GET/PATCH alert-settings.

## User API

- `GET /api/user/projects/{project_id}/alert-settings` — read project and environment-level alert settings (**owner only**).
- `PATCH /api/user/projects/{project_id}/alert-settings` — update project-level and optional environment-level settings (**owner only**).
