# Usage limiting

## Overview

Event storage is limited per user plan (Free, Basic, Teams, Teams Pro). Limits are enforced at ingest; the dashboard can show current usage via a dedicated API.

## Flow

1. On `POST /api/{project_id}/store/`, the project owner is resolved (if any).
2. Current event count for that user (across all their projects) is computed.
3. User’s limit is derived from `User.plan` (e.g. Free: 1,000; Basic: 15,000; Teams: 25,000; Teams Pro: 50,000).
4. If `current_count + 1 > limit`, the request returns 403 and the event is not stored.
5. If the user is near the limit (e.g. ≥ 80%), a warning is included in the response body.

## Key components

- **Constants:** `src/xrayradar_server/constants.py` — `TIER_EVENT_LIMITS`, `TIER_WARNING_THRESHOLD`
- **Logic:** `src/xrayradar_server/usage.py` — `get_user_event_count`, `get_user_event_limit`, `check_user_event_limit`, `is_near_limit`
- **Enforcement:** `src/xrayradar_server/routers/api.py` — `store_event` (before adding the event)
- **Usage API:** `GET /api/user/usage` in `src/xrayradar_server/routers/user_api.py` — returns current_count, limit, plan, is_exceeded, is_near_limit, percentage_used

## Data

- Count includes **all event levels** (error, warning, info, debug) across all projects owned by the user.
- No new tables; uses existing `User.plan` and `Event` rows.
