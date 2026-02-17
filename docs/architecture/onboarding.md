# User onboarding guidance

## Overview

New signed-up users are guided through a consistent 3-step setup so they can start sending events and viewing issues. Guidance is shown in the dashboard UI and reinforced by a one-time email sent immediately after email verification.

## Setup steps

The product flow assumes:

1. **Create a project** — User creates a project from the dashboard (Projects page). Project creation requires a verified email.
2. **Request a token** — User requests an API token from an admin via the Tokens page. Tokens are issued by an admin; the user sees pending and fulfilled requests.
3. **Assign token to project** — Once a token is issued, the user grants that token access to their project(s) from the Tokens page (Manage project access). Events sent with that token are then associated with the project and appear in the dashboard.

## Dashboard “Getting started” card

- **Where:** Dashboard home (`/dashboard`), in the main content area.
- **When shown:** When the user has no events in the last 30 days (`stats.totals?.last_30d === 0`). This targets new or inactive users who have not yet sent events.
- **Content:**
  - Title: “Getting started”
  - Short intro: “Set up your first project in three steps.”
  - Numbered list: (1) Create a project in Projects, (2) Request a token from an admin in Tokens, (3) Assign token access to your project from Tokens.
  - Two CTAs: “Create project” (links to `/dashboard/projects`) and “Request and assign token” (links to `/dashboard/tokens`).
- **Implementation:** `xrayradar-web/src/pages/DashboardHome.jsx` — same condition as the existing empty-state card; copy and links were expanded to the 3-step checklist and dual CTAs.

## Post-verification onboarding email

- **Trigger:** Immediately after successful email verification. When the user clicks the link in the verification email, `GET /auth/verify-email?token=...` runs, sets `User.email_verified = True`, clears the verification token, sets the session cookie (so the user is logged in), then enqueues a single onboarding email job and runs the email job processor in the background. The user can click “Go to dashboard” on the success page without signing in again.
- **Recipient:** The user who just verified (same email as the verified account).
- **Frequency:** One-time per user; the job is only enqueued on the first successful verification (already-verified users get “Email already verified” and no job is enqueued).
- **Content (high level):**
  - Subject: “[XrayRadar] Getting started in 3 steps”
  - Body: Short confirmation that their email is verified, then the same 3 steps (create project, request token, assign token to project) with direct links to dashboard, Projects, and Tokens. CTA: “Open dashboard” linking to `{XRAYRADAR_BASE_URL}/dashboard`.
- **Delivery:** Same pipeline as other transactional emails: job type `post_verification_onboarding` in `email_jobs`, sent via Resend by `process_pending_email_jobs`, with retries and logging in `email_log` (type `post_verification_onboarding`).

## Key components

- **Backend**
  - **Verify flow:** `src/xrayradar_server/routers/user_auth.py` — `verify_email` enqueues the onboarding job via `_enqueue_post_verification_onboarding_email` and calls `background_tasks.add_task(process_pending_email_jobs)`.
  - **Template:** `src/xrayradar_server/email_templates.py` — `render_post_verification_getting_started_email(base_url)`.
  - **Mail jobs:** `src/xrayradar_server/mail_jobs.py` — handling for `job_type == "post_verification_onboarding"` (single recipient, no token in payload; logs to `email_log` with `email_type="post_verification_onboarding"`).
- **Frontend**
  - **Dashboard card:** `xrayradar-web/src/pages/DashboardHome.jsx` — “Getting started” section with 3-step list and links to Projects and Tokens.
- **Config:** Uses existing `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `XRAYRADAR_BASE_URL`; no new env vars. If Resend is not configured, the onboarding job is still enqueued but delivery will fail and be retried according to the usual email job policy.

## Related

- [Auth](auth.md) — Signup, verify-email, and session; verification triggers the onboarding email.
- [Environments, Env ACL, and notifications](environments-acl-notifications.md) — Email job queue and `post_verification_onboarding` job type.
