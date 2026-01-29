# Event ingest

## Overview

Events are sent by client applications to the ingest endpoint and stored with a computed fingerprint for grouping into issues.

## Flow

1. Client sends `POST /api/{project_id}/store/` with an event payload (message, level, timestamp, contexts, etc.).
2. Request is authorized via `X-Xrayradar-Token` (project or admin token).
3. Usage limits are checked for the project owner (if any).
4. Fingerprint is computed from the event (exception type/value, message, stack).
5. Event row is written to `events` and committed.
6. Optional: email alert logic runs in the background if configured (see [Email alerts](email-alerts.md)).

## Key components

- **API:** `src/xrayradar_server/routers/api.py` — `store_event`
- **Fingerprinting:** `src/xrayradar_server/fingerprinting.py` — `compute_fingerprint`
- **Models:** `src/xrayradar_server/models.py` — `Event`, `Project`

## Related

- [Usage limiting](usage-limiting.md) — enforced during ingest
- [Email alerts](email-alerts.md) — triggered after commit when level is error
