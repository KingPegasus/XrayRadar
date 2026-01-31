# Account deletion

## Overview

Users can request account deletion from the dashboard. A pending request is stored; an admin reviews and fulfills it from the admin UI. Fulfilling permanently deletes the user and all associated data.

## Flow

1. **Request:** User (verified) calls `POST /api/user/deletion-request` with optional `reason`. Only one pending request per user; duplicate returns 400.
2. **Status:** `GET /api/user/deletion-request` returns the current pending request (or `null` if none).
3. **Cancel:** User can cancel with `DELETE /api/user/deletion-request` before fulfillment.
4. **Admin list:** Admin calls `GET /api/admin/deletion-requests` (or uses admin UI “Deletions” view) to see pending requests (user email, reason, created_at).
5. **Fulfill:** Admin calls `POST /api/admin/deletion-requests/{request_id}/fulfill`. Backend deletes all events for the user’s projects, then deletes the user (cascades: projects, token_requests, deletion_requests; tokens linked via `user_id` are handled by DB or explicit cleanup as implemented).

## Data removed on fulfillment

- All events for projects owned by the user
- User row (cascades remove projects, token_requests, deletion_requests, and any user-linked tokens)

## Key components

- **User API:** `src/xrayradar_server/routers/user_api.py` — `user_request_deletion`, `user_get_deletion_request`, `user_cancel_deletion_request`
- **Admin API:** `src/xrayradar_server/routers/admin_api.py` — `admin_list_deletion_requests`, `admin_fulfill_deletion_request`
- **Models:** `src/xrayradar_server/models.py` — `DeletionRequest` (user_id, reason, created_at, fulfilled_at, cancelled_at)
- **Admin UI:** `src/xrayradar_server/admin_ui.py` — “Deletions” view lists requests and provides fulfill action

## Related

- [Auth](auth.md) — Deletion request requires verified user
- [Admin](admin.md) — Fulfillment is done via admin API/UI
