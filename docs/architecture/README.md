# Architecture

This folder documents the architecture of XrayRadar features. Each document describes a feature area with data flow, components, and diagrams where applicable.

## Contents

| Document | Description |
|----------|-------------|
| [Event ingest](event-ingest.md) | Event storage API, fingerprinting, and persistence |
| [Dashboard stats](dashboard-stats.md) | Dashboard error statistics: totals, trends, top errors, 30-day frequency chart |
| [Breadcrumbs](breadcrumbs.md) | Breadcrumb trail capture, storage, and timeline display |
| [Email alerts](email-alerts.md) | Email notifications for errors via Resend (project owner + additional recipients) |
| [Usage limiting](usage-limiting.md) | Event storage limits per plan tier (Free / Basic / Pro) |
| [Rate limiting](rate-limiting.md) | IP- and token-based rate limits for auth and event ingest (429) |
| [Event frequency](event-frequency.md) | 30-day event frequency charts (project and issue views) |
| [Issue status](issue-status.md) | Issue lifecycle management: status tracking, release-based resolution, auto-reopen |
| [Auth](auth.md) | User authentication: signup, login, session, email verification, password reset |
| [Account deletion](account-deletion.md) | User deletion requests and admin fulfillment |
| [Admin](admin.md) | Admin UI (GitHub OAuth) and admin API (tokens, users, token requests, deletion requests) |
| [Teams / Teams Pro access](pro-team-access.md) | Teams plans: team members, project assignment, invites, accept-invite flow, multi-team membership |

## Diagram format

Diagrams use [Mermaid](https://mermaid.js.org/) syntax (sequence diagrams, flowcharts). They render in GitHub, GitLab, and many Markdown viewers.
