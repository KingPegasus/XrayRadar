# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.17.0] - 2026-03-28

### Changed

- **Email templates**
  - HTML emails now use the new PNG logo for branding in the header.
  - When `XRAYRADAR_BASE_URL` is localhost (or otherwise unsuitable for loading remote images), templates show a **text “XrayRadar” fallback** instead of a broken logo image.

## [0.16.0] - 2026-03-08

### Added

- **Admin new-user signup notification**
  - When a new user signs up, all admins listed in `XRAYRADAR_ADMIN_EMAILS` receive an email notification with the new user's email, plan, and signup time. Uses the existing durable email job queue (`admin_new_user` job type). Architecture docs updated (auth, admin) with data-flow diagram.
- **Admin token-request notification**
  - When a user requests an API token (`POST /api/user/token-requests`), all admins in `XRAYRADAR_ADMIN_EMAILS` receive an email with the requester's email, token name, note, request ID, and requested-at time. Uses the durable email job queue (`admin_token_request` job type). CTA links to the admin Token requests view (`/admin#requests`).


## [0.15.0] - 2026-03-01

### Added

- **Android and Kotlin SDK support (frontend)**
  - Landing page now includes Android/Kotlin as a supported SDK with quick-setup snippet, framework selector (Kotlin), and SDK card with feature summary and link to the [XrayRadar Android SDK](https://github.com/KingPegasus/XrayRadar-Android-SDK) repository.
  - New Kotlin and Android logos in the framework picker and SDK section.
- **CI coverage badge automation**
  - CI workflow now extracts backend and frontend coverage percentages from test runs and uploads them as artifacts.
  - New `update-badges` job (on pull requests) updates the README coverage badge URLs with the computed percentages and color, then commits the change to the PR branch.

### Changed

- **update-coverage.yml**
  - Streamlined badge-update logic and removed unnecessary checks for a simpler manual refresh path.

### Fixed

- **Frontend coverage badge**
  - Corrected the frontend coverage badge URL in README so it displays the proper shields.io badge.

## [0.14.0] - 2026-02-17

### Added

- **User onboarding guidance**
  - Added a richer "Getting started" checklist on Dashboard Home for signed-up users with direct actions to Projects and Tokens.
- **Post-verification onboarding email**
  - Added a one-time onboarding email sent immediately after successful email verification with setup steps (create project, request token, assign token access).

### Fixed

- **Alert settings (Basic plan)**
  - PATCH alert-settings no longer returns "Environment-based alert settings are available only on Teams and Teams Pro plans" when a Basic user saves project-level settings (e.g. additional emails). Sending an empty `environment_settings` list is now allowed; only non-empty environment settings are restricted to Teams/Teams Pro.
- **Post-verification “Go to dashboard”**
  - `GET /auth/verify-email` now sets the session cookie so the user is logged in after verifying their email; “Go to dashboard” on the success page works without signing in again. Dashboard route redirect to login when unauthenticated is performed in a `useEffect` to avoid a blank frame.

## [0.13.0] - 2026-02-15

### Added

- **SEO**
  - Added `robots.txt` (Allow /) for crawler guidance.
- **Optional user in auth**
  - Optional user retrieval in dependencies; unauthenticated requests can resolve to no user without failing.

### Changed

- **Environment-specific alert settings (plan-gated)**
  - New user plan checks for environment-specific alert settings: only Teams and Teams Pro plans can access these features.
- **Alert scheduling**
  - Enhanced alert scheduling to prevent duplicate emails within a 90-second window.
- **User authentication API**
  - `GET /api/me` now returns 200 with body `null` when unauthenticated (instead of 401); user auth routes updated to use optional user dependency where appropriate.
- **Frontend performance**
  - Lazy loading for key components and routes (React.lazy + Suspense) to reduce initial bundle and improve load time.

## [0.12.0] - 2026-02-14

### Added

- **Project environment views and filtering**
  - Environment selector on project issues and issue detail pages, with query param and localStorage persistence.
  - New `GET /api/user/projects/{project_id}/environments` endpoint for environment list/count/last_seen.
  - Environment filtering support for issue/events/frequency/breakdown user endpoints.
- **Environment-level access control (Env ACL)**
  - Member env ACL model and APIs: `project_member_environments` + owner management endpoints.
  - Token env ACL model and APIs: `token_project_environment_access` + read/replace endpoints.
  - Backend enforcement for user read paths and token ingest environment scoping.
- **Token environment scope management in UI**
  - Tokens page now supports per-token/per-project environment configuration with a modern inline selector.
  - Clear unrestricted behavior when no environments are selected ("All environments").
- **Durable email delivery queue**
  - New `email_jobs` table and worker utility with retry/backoff processing.
  - Alert/auth email flows updated to use job enqueue + async processing.

### Changed

- **Alerts become environment-aware**
  - Added optional env-level alert settings and recipients.
  - Alert subject/body can include environment context.
- **Project settings save feedback in UI**
  - Added visible success confirmation when alert settings are saved.
  - Added visible success confirmation when environment access settings are saved.
  - Project settings modal is now organized into collapsible sections (Project name, Environment access, Email alerts) for better scanability.
- **Token UX improvement**
  - Tokens page now includes a copy action for token values with inline "Copied" feedback.
- **Alert delivery refinement**
  - Error alerts now send as cooldown-window digests (top issues since last successful alert) instead of single-event email bodies.
  - Digest rendering uses a shared modern template module with optional logo fallback.
  - Added robust alert scheduler state + periodic evaluator path (`alert_schedule_state`, `alert_scheduler`) to enqueue due digests from an in-process scheduler loop in the web app.
  - Added scheduler env controls (`XRAYRADAR_SCHEDULER_ENABLED`, `XRAYRADAR_SCHEDULER_INTERVAL_SECONDS`) and a one-shot worker script `scripts/run_alert_scheduler_once.py` for manual/optional external runs.
  - 90-second enqueue debounce per project/environment (`last_enqueued_at`) to avoid duplicate emails when ingest and scheduler both fire; empty digests are no longer sent.
  - Enforced exclusive scope routing in scheduler evaluation: project-level digests now exclude events in environments that have their own enabled env-level alert settings, preventing duplicate owner emails for the same env event stream.
  - Alert settings UI now clearly separates project-wide and environment-specific configuration, and documents email subject mapping in the UI.
- **Alert settings access control**
  - `GET/PATCH /api/user/projects/{project_id}/alert-settings` now require project ownership.
  - Project members no longer see Email Alert Settings in `ProjectSettingsModal`.
- **Architecture docs expanded**
  - Added `docs/architecture/environments-acl-notifications.md`.
  - Updated architecture docs for email alerts, team access, and event frequency.

---

## [0.11.0] - 2026-02-08

### Added

- **Project name update (owner only)**
  - New `PATCH /api/user/projects/{project_id}` endpoint to update project name; only the project owner can update.
  - Frontend: project name editing in ProjectSettingsModal (owner-only) and ProjectIssuesPage; page title updates after save.
  - Tests for owner update success and non-owner (member) receiving 404.

### Changed

- **CORS for browser ingest**
  - CORS middleware enabled so browser apps (e.g. React) on any origin can `POST` to `/api/{project_id}/store/`; auth remains by `X-Xrayradar-Token` only.
- **Token–project access**
  - Only project owners can assign tokens to projects (members no longer can); tests added for member-forbidden grant/revoke.

---

## [0.10.0] - 2026-02-08

### Added

- **SDK logos and quick setup snippets on landing page**
  - Introduced SVG logos for FastAPI, Django, Flask, Node.js, React, and Next.js to enhance the landing page.
  - Implemented a new `FrameworkLogo` component to render these logos dynamically.
  - Added quick setup code snippets for each SDK in the `SDK_FRAMEWORKS` utility, improving onboarding experience.
  - Updated the LandingPage component to include SDK integration details and quick setup instructions.
  - Enhanced constants for features to reflect SDK support in both Python and JavaScript/TypeScript.

---

## [0.9.0] - 2026-02-07

### Added

- **Project members and team invites for Teams plan**
  - Introduced `project_members` and `team_invites` tables to manage team access and invitations for users on the Teams and Teams Pro plans.
  - Implemented database migrations to create necessary tables and columns.
  - Updated user models and relationships to support team membership and invites.
  - Enhanced API endpoints to handle team member management and invite acceptance.
- **Teams and Teams Pro plans**
  - Renamed Pro plan to **Teams** ($5/month, 25k events, 5 members).
  - New **Teams Pro** tier ($7/month, 50k events, 10 members).
  - Team member limits enforced per plan; `require_teams_plan` dependency for team-only endpoints.
- **Email alerts by plan**
  - Free: email alerts disabled (upgrade message in project settings).
  - Basic: 10-minute cooldown; Teams/Teams Pro: 1-minute cooldown.
  - Backend constants and notification logic updated; frontend EmailAlertSettings reflects plan limits.
- **Admin dashboard**
  - System stats include team invite email count; dashboard shows “Last updated,” clickable cards, and improved layout.
  - Users tab: plan filter and badges updated to Free / Basic / Teams / Teams Pro.

### Changed

- Migration `0011_rename_pro_plan_to_teams` renames Pro to Teams in the database.
- Migration `0010_project_members_team_invites`: `alembic_version.version_num` widened to VARCHAR(64) for long revision IDs.

---

## [0.8.0] - 2026-02-06

### Added

- **Rate limiting for public endpoints**
  - IP-based rate limiting for authentication endpoints (signup, login, forgot-password, reset-password, verify-email, resend-verification)
  - Token-based rate limiting for event ingestion (`POST /api/{project_id}/store/`)
  - Configurable via `XRAYRADAR_RATE_LIMIT_AUTH` and `XRAYRADAR_RATE_LIMIT_EVENT_INGEST` (e.g. `5/minute`, `100/minute`)
  - Implemented with `slowapi`; returns 429 when limits are exceeded
- **Email logging and admin dashboard statistics**
  - `EmailLog` model to track email notifications (type, recipient, success status, error messages)
  - `send_alert_emails` and user auth email flows now log to EmailLog
  - Admin API endpoint for system statistics (projects, tokens, users, events, email counts)
  - Admin UI dashboard view displaying system statistics
- **Issue status management and auto-reopen**
  - `IssueStatus` model for issue lifecycle (status, resolved release, timestamps)
  - Endpoints to update and bulk-update issue status; auto-reopen on new events when applicable
  - Architecture docs updated for issue status and API behavior
- **Token project access revocation**
  - `POST /api/user/tokens/{token_id}/projects/{project_id}/revoke` for revoking a token’s project access
  - TokensPage “Revoke access” button when a token has access to a project
  - Admin UI: `#tokens` hash routing fixed so `/admin#tokens` shows the tokens view

### Fixed

- **Event frequency and UI date handling** — Frequency queries now extract dates in UTC (PostgreSQL `AT TIME ZONE 'UTC'`); frontend builds the 30-day range in UTC so the latest date (e.g. today) appears correctly in the chart. SQLite tests use plain `date()` for compatibility.
- **Email alert cooldown and project-level limit** — Cooldown enforced; project-level alert limits applied as intended.

---

## [0.7.0] - 2026-01-27

### Added

- **Breadcrumbs feature** — Enhanced error context with event trails leading to exceptions
  - `BreadcrumbIn` schema for validation (timestamp, type, category, message, level, data)
  - Breadcrumb normalization in event ingestion: limit 100, truncate messages to 1024 chars, default type/level
  - Event storage in `payload.breadcrumbs` (JSONB)
  - Architecture docs: `docs/architecture/breadcrumbs.md`
  - `scripts/send_console_breadcrumb.py` — Send test events with console-type breadcrumbs
- **BreadcrumbTimeline component** — Frontend timeline for breadcrumbs in event detail view
  - Chronological display with sort toggle (oldest/newest first)
  - Type icons (http, ui, navigation, error, console, etc.)
  - Level color-coding (debug, info, warning, error)
  - Relative timestamps ("5s before error")
  - Expandable data sections
- **Protected API docs** — `/docs` and `/redoc` require admin session; OpenAPI schema admin-only
- **User API refactor** — Modular router structure
  - `account`, `alerts`, `dashboard`, `issues`, `projects`, `tokens` routers
  - `user_owned_project_ids_subq` helper for authorization
  - Dashboard statistics schemas (totals, trends, top errors)
- **IssueBreakdown component** — Breakdown data display on issue detail page

### Changed

- Raw Event Data: Copy button stays fixed at top; JSON content scrolls in scrollable container
- EventDetailView: Breadcrumb section layout; improved JSON copy UX
- User API: Split monolithic `user_api.py` into focused modules
- Frontend: Updated coverage thresholds in vite.config.js; improved styling and component rendering
- `scripts/send_real_error.py`: Breadcrumb payload structure updates

---

## [0.6.0] - 2026-02-01

### Added

- **Password reset flow** — Users can reset forgotten passwords via email
  - `POST /auth/forgot-password` — Request a password reset link (body: `{"email":"..."}`). Always returns 200 to avoid email enumeration.
  - `POST /auth/reset-password` — Set new password with token from email (body: `{"token":"...","new_password":"..."}`). Tokens expire in 1 hour.
  - Forgot Password page (`/forgot-password`) with email form and success confirmation
  - Reset Password page (`/reset-password?token=...`) with new password form
  - "Forgot password?" link on the login page
  - Password reset emails sent via Resend (when configured)
- **Event storage limits and usage tracking** — Enforce event limits by subscription tier (Free/Basic/Pro)
  - `GET /api/user/usage` — Returns current event count, limit, and plan
  - Usage widget and event frequency charts in dashboard
  - `scripts/recompute_fingerprints.py` — Recompute fingerprints to align with current logic
- **Email alert settings and recipient management**
  - Project alert settings (enabled, level filter, cooldown)
  - Additional alert recipients per project
  - Non-blocking email notifications for error-level events via Resend
  - Architecture docs: `docs/architecture/email-alerts.md`
- **Email verification**
  - Verification emails at signup with secure tokens
  - `GET /auth/verify-email?token=...` — One-time verification link
  - `POST /auth/resend-verification` — Resend verification email (requires login)
  - VerifyEmailPage and EmailVerificationBanner in frontend
- **Account deletion flow**
  - Users can request account deletion; admins fulfill requests
  - `DeletionRequest` model and admin API for fulfillment
  - Architecture docs: `docs/architecture/account-deletion.md`
- **Architecture documentation** — `docs/architecture/` for event-ingest, usage-limiting, event-frequency, auth, account-deletion, admin, email-alerts
- **Database migrations** — `0003_project_alert_settings`, `0004_user_email_verification`, `0005_deletion_requests`, `0006_password_reset`

### Changed

- Version bumped from 0.5.0 to 0.6.0
- README updated with all new flows, endpoints, and configuration
- ROADMAP updated; password reset marked complete
- User model: `email_verified`, `verification_token`, `password_reset_token`, `password_reset_expires_at`
- Added Resend dependency for verification and alert emails

---

## [0.5.0] - 2026-01-27

### Added

- **Admin API test suite** — Comprehensive tests for admin endpoints (tokens, users, token requests, deletion requests, events)
- **Frontend test coverage** — Tests for LoginPage, ProjectsPage, TokensPage, EventDetailPage, IssueDetailPage, ProjectIssuesPage, LandingPage, Logo, SignupModal, DashboardLayout
- **Logo component** — New `Logo.jsx` with fallback text on image load errors
- **Assets** — `logo.svg` and `logo_square.svg` for branding

### Changed

- Version bumped from 0.4.0 to 0.5.0
- Enhanced Logo handling in UI for better error resilience
- Improved DashboardLayout, LandingPage, and styles for consistency

---

## [0.4.0] - 2026-01-26

### Added

- **Logo component** — Consistent branding across the application
- **Web routing improvements** — Selective registration of catch-all routes in `web.py`
- **Tests** — New tests for routing behavior and blocked paths (`test_web_marketing.py`, `test_main_misc.py`)

### Changed

- Version bumped from 0.3.0 to 0.4.0
- Improved web routing logic to allow selective catch-all route registration
- Enhanced DashboardLayout, LandingPage, and styles

---

## [0.3.0] - 2026-01-25

### Added

- **Token request management** — Users request tokens via dashboard; admins fulfill requests
  - `TokenRequest` model and admin API endpoints
  - Admin UI view for listing and fulfilling token requests
- **Fingerprinting** — Event grouping by fingerprint (exception type, message, stack frame)
- **Admin UI and event management** — Project events listing, filtering, detail modal
  - `GET /api/admin/projects/{id}/events` and `GET /api/admin/projects/{id}/events/{event_id}`
  - `scripts/send_test_event.py` — Send test events to ingestion endpoint
- **Test coverage** — pytest-cov integrated into CI

### Changed

- Version bumped from 0.2.0 to 0.3.0
- Admin UI layout and event management improvements

---

## [0.2.0] - 2026-01-17

### Added

- **User authentication** — Email/password signup and login for dashboard users; session cookies
- **Web marketing site** — Landing page, signup modal; served by FastAPI
- **Alembic migrations** — Schema migrations for Render/Docker deployments
- **GitHub OAuth admin UI** — Admin login via GitHub; session cookie with email allowlist
- **Token email metadata** — Tokens can be associated with user emails
- **Production hardening**
  - Secure cookies via `XRAYRADAR_ENV` / `XRAYRADAR_COOKIE_SECURE`
  - Uvicorn proxy headers for Render
  - Docker image runs as non-root user
- **Dependencies** — httpx, itsdangerous, alembic; version pinning with upper bounds
- **Tests** — Expanded test fixtures; 100% backend coverage

### Changed

- Version bumped from 0.1.0 to 0.2.0
- Dependency constraints and uv.lock

---

## [0.1.0] - 2026-01-12

### Added

- **Basic server functionality** — FastAPI server with event storage
- **Token-based authentication** — `X-Xrayradar-Token` header for API access
- **Health endpoint** — `GET /health` with `auth_required` flag

---

[0.17.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.7.0...v0.8.0
