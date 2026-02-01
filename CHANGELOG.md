# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.7.0]: https://github.com/your-org/xrayradar-server/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/your-org/xrayradar-server/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/your-org/xrayradar-server/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/your-org/xrayradar-server/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/your-org/xrayradar-server/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/your-org/xrayradar-server/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/your-org/xrayradar-server/releases/tag/v0.1.0
