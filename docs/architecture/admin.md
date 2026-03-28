# Admin UI and API

## Overview

Administration is available via a web UI (GitHub OAuth) and via API using an admin token (`X-Xrayradar-Token` with `is_admin=True`). Both use the same `require_admin` dependency.

## Admin authentication

- **Web UI:** User visits `/admin`; if not logged in, redirected to `/auth/github/login`. GitHub OAuth callback sets `xrayradar_session` cookie; email must be in `XRAYRADAR_ADMIN_EMAILS` (comma-separated). Session admin is treated as an admin “token” with no secret.
- **API:** Request includes header `X-Xrayradar-Token` with a token that has `is_admin=True` and is not revoked.

### GitHub OAuth App registration

The server does not create the OAuth App for you. Register one on GitHub and wire it with environment variables (see also [DEVELOPERS.md](../../DEVELOPERS.md) for deployment context).

1. **Create an OAuth App**  
   - Personal account: GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**.  
   - Organization (recommended for teams): **Organization settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**.  
   - Official reference: [Creating an OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).

2. **Application name / Homepage URL**  
   - Use your product name and the public base URL users see (e.g. `https://your-domain.com` or `http://localhost:8001` for local dev).

3. **Authorization callback URL**  
   - Must **exactly** match `XRAYRADAR_GITHUB_REDIRECT_URI` (same scheme `http` vs `https`, host, port if any, and path). GitHub rejects mismatches; the app sends this value on authorize and token exchange (`main.py`).  
   - Path is always the backend route: **`/auth/github/callback`**.  
   - Examples:  
     - Local: `http://localhost:8001/auth/github/callback`  
     - Production: `https://your-domain.com/auth/github/callback`

4. **Copy credentials into the server**  
   - **Client ID** → `XRAYRADAR_GITHUB_CLIENT_ID`  
   - **Client secret** (generate on GitHub) → `XRAYRADAR_GITHUB_CLIENT_SECRET`  
   - **Callback** (same string as in step 3) → `XRAYRADAR_GITHUB_REDIRECT_URI`

5. **Scopes**  
   - The app requests `read:user` and `user:email` so it can read the user’s **verified** email addresses from the GitHub API. No extra scopes are required for admin login.

6. **Allowlist**  
   - After OAuth succeeds, the **primary verified** GitHub email (or first verified email) is normalized to lowercase and must appear in `XRAYRADAR_ADMIN_EMAILS`; otherwise the callback returns 403.

7. **Local HTTP**  
   - For `http://` dev URLs, set `XRAYRADAR_COOKIE_SECURE=false` so OAuth state and session cookies work (see `auth.cookie_secure()`).

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

## Admin email notifications

Admins configured via `XRAYRADAR_ADMIN_EMAILS` receive emails for two events:

- **New user signup** — When a new dashboard user signs up, admins get an email with the user's email, plan, and signup time. Delivered via the durable email job worker (`admin_new_user` job type). For the full flow, see [Auth](auth.md#signup-email-job-data-flow).
- **Token request** — When a user requests an API token (`POST /api/user/token-requests`), admins get an email with the requester's email, token name, note, request ID, and requested-at time. Delivered via the same worker (`admin_token_request` job type). The email CTA links to `/admin#requests` so admins can fulfill the request.

## Key components

- **Main:** `src/xrayradar_server/main.py` — `/auth/github/login`, `/auth/github/callback`, `/admin`, `/api/admin/me`
- **Admin UI:** `src/xrayradar_server/admin_ui.py` — Renders admin SPA HTML
- **Admin API:** `src/xrayradar_server/routers/admin_api.py` — All `/api/admin/*` routes
- **Auth/deps:** `src/xrayradar_server/auth.py` — session serializer; `deps.py` — `require_admin`, `_is_session_admin`, `parse_admin_allowlist`
- **Config:** `XRAYRADAR_GITHUB_CLIENT_ID`, `XRAYRADAR_GITHUB_CLIENT_SECRET`, `XRAYRADAR_GITHUB_REDIRECT_URI`, `XRAYRADAR_ADMIN_EMAILS`, `XRAYRADAR_SESSION_SECRET`

## Related

- [Account deletion](account-deletion.md) — Fulfillment via admin
- [Auth](auth.md) — User auth is separate (email/password for dashboard users)
