# Admin UI and API

## Overview

Administration is available via a web UI (GitHub OAuth) and via API using an admin token (`X-Xrayradar-Token` with `is_admin=True`). Both use the same `require_admin` dependency.

## Admin authentication

- **Web UI:** User visits `/admin`; if not logged in, redirected to `/auth/github/login`. GitHub OAuth callback sets `xrayradar_session` cookie; email must be in `XRAYRADAR_ADMIN_ALLOWLIST` (comma-separated). Session admin is treated as an admin “token” with no secret.
- **API:** Request includes header `X-Xrayradar-Token` with a token that has `is_admin=True` and is not revoked.

## Admin UI (SPA)

- **Entry:** `GET /admin` — Renders HTML that loads the admin SPA (see `admin_ui.py`).
- **Views:** Tokens, Token requests, Users, Deletions, Logs. Each view calls the corresponding admin API endpoints.
- **Token requests:** List requests; “Fulfill” creates a token for the requesting user and marks the request fulfilled (user sees the token value once in the UI response).
- **Users:** List users with plan and event count; change plan via `PATCH /api/admin/users/{user_id}/plan`.
- **Deletions:** List pending deletion requests; “Fulfill” runs fulfillment (see [Account deletion](account-deletion.md)).

## Admin API endpoints

| Area | Endpoints |
|------|-----------|
| Tokens | `POST /api/admin/tokens`, `GET /api/admin/tokens`, `POST /api/admin/tokens/{id}/revoke` |
| Projects | `GET /api/admin/projects`, `POST /api/admin/tokens/{token_id}/projects/{project_id}/grant`, `POST .../revoke` |
| Token requests | `GET /api/admin/token-requests`, `POST /api/admin/token-requests/{request_id}/fulfill` |
| Users | `GET /api/admin/users`, `PATCH /api/admin/users/{user_id}/plan` |
| Deletion requests | `GET /api/admin/deletion-requests`, `POST /api/admin/deletion-requests/{request_id}/fulfill` |

Additional admin-only endpoints exist for listing project events and token–project access; see `admin_api.py`.

## Key components

- **Main:** `src/xrayradar_server/main.py` — `/auth/github/login`, `/auth/github/callback`, `/admin`, `/api/admin/me`
- **Admin UI:** `src/xrayradar_server/admin_ui.py` — Renders admin SPA HTML
- **Admin API:** `src/xrayradar_server/routers/admin_api.py` — All `/api/admin/*` routes
- **Auth/deps:** `src/xrayradar_server/auth.py` — session serializer; `deps.py` — `require_admin`, `_is_session_admin`, `parse_admin_allowlist`
- **Config:** `XRAYRADAR_GITHUB_CLIENT_ID`, `XRAYRADAR_GITHUB_CLIENT_SECRET`, `XRAYRADAR_GITHUB_REDIRECT_URI`, `XRAYRADAR_ADMIN_ALLOWLIST`, `XRAYRADAR_SECRET_KEY`

## Related

- [Account deletion](account-deletion.md) — Fulfillment via admin
- [Auth](auth.md) — User auth is separate (email/password for dashboard users)
