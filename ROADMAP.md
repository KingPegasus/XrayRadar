# Roadmap

This document tracks pending and future features for XrayRadar.

## Completed Features

_Features that have been implemented._

### Authentication & Security

1. **Email verification for newly sign-up users** ✅
   - Verify email addresses during user registration
   - Send verification email with confirmation link
   - Prevent unverified accounts from accessing the platform

2. **Password reset flow** ✅
   - Allow users to reset forgotten passwords
   - Send password reset email with secure token
   - Implement secure password reset endpoint

3. **Rate limiting** ✅
   - IP-based rate limiting for auth endpoints (signup, login, forgot-password, reset-password, verify-email, resend-verification)
   - Token-based rate limiting for event ingestion (`POST /api/{project_id}/store/`)
   - Configurable via `XRAYRADAR_RATE_LIMIT_AUTH` (default: 5/minute) and `XRAYRADAR_RATE_LIMIT_EVENT_INGEST` (default: 100/minute)
   - Returns 429 Too Many Requests when limit exceeded (slowapi)

### Dashboard & Analytics

4. **Dashboard graphs for showing error statistics** ✅
   - Total errors (last 24h / 7d / 30d)
   - Unique issues count
   - Error trend graph (up/down vs previous period)
   - Top 5 errors by frequency

### Notifications

5. **Email alerts for errors** ✅
   - Configure email notifications for error events
   - Set up alerting rules and thresholds
   - Send email notifications when errors occur
   - Cooldown per issue and per project (no email before configured minimum; project-level prevents multiple issues from triggering emails within the same window)
   - Cooldown state persisted in DB (survives server restart)
   - Plan-based: **Free** (alerts disabled; upgrade message in settings), **Basic** (10 min cooldown), **Teams/Teams Pro** (1 min cooldown)

### Issue Management

6. **Issue status management** ✅
   - Mark issues as: Open, In Progress, Resolved, Ignored
   - Resolved state with optional “resolved until next release” tracking
   - Auto-reopen when new events occur (e.g. after resolution, by release)
   - Bulk update status (resolve/ignore multiple)
   - UI: status badge, change-status modal, project issues table with bulk actions

### Usage & Limits

7. **Usage limiting for events stored per basic or free account** ✅
   - Implement event storage limits for free/basic tiers
   - Track event count per account (all event levels: error, warning, info, debug)
   - Enforce limits and notify users when approaching limits
   - **Teams** and **Teams Pro** tiers with per-plan event and member limits (25k/5 members and 50k/10 members)

### SDK & Integrations

8. **Official Python SDK** ✅ _(in [xrayradar](https://github.com/xrayradar/xrayradar) repo)_
   - High-level API: `capture_exception()`, `capture_message()`, `init()`, DSN-based config
   - Breadcrumbs: `add_breadcrumb()`, `clear_breadcrumbs()`, `max_breadcrumbs`; sent with every event
   - Context: `set_user()`, `set_tag()`, `set_extra()`, `set_context()`; environment, release, server_name
   - Global uncaught-exception handler, `before_send` callback, sampling, client-side fingerprinting
   - HTTP transport (not raw POST), payload truncation, rate-limit handling
   - Framework integrations: **Django**, **FastAPI**, **Flask**, **Django REST Framework**, **Graphene**, **Logging** (auto breadcrumbs per request, exception handlers, request context)

### Context & Debugging

9. **Breadcrumbs** ✅
   - Capture trail of events leading to error (SDK buffer → payload → storage)
   - Automatic breadcrumbs: **HTTP/network requests** via Django/FastAPI/Flask middleware (one breadcrumb per request)
   - Custom breadcrumbs via SDK: `add_breadcrumb()`, `clear_breadcrumbs()`, `max_breadcrumbs` config
   - Breadcrumb timeline in **event** detail view (BreadcrumbTimeline: type icons, level colors, relative time, expandable data, sort toggle)
   - _Note: Automatic clicks, navigation, and console logs would require a JavaScript SDK (not yet implemented); Python SDK supports manual breadcrumbs for any type._

### Team & Access

10. **Team plans, project members, and invites** ✅ _(v0.9.0)_
    - **Teams** ($5/mo) and **Teams Pro** ($7/mo) plans with event and member limits (25k/5 and 50k/10)
    - Project members: add and remove members to/from projects (Teams/Teams Pro only)
    - Team invites: invite by email; accept/decline flow; multi-team membership supported
    - Database: `project_members` and `team_invites` tables; migrations and API for member management and invite acceptance
    - Admin: team invite email stats, Users tab plan filter and badges (Free / Basic / Teams / Teams Pro)

---

## Pending Features

_Features that are planned for upcoming releases, organized by priority._

### Priority 1: Core Functionality (High Impact)

#### Issue Management & Workflow

1. **Issue assignment**
   - Assign issues to team members
   - Auto-assignment rules based on file path, error type, or project
   - Team/role-based assignment
   - Assignment notifications
   - _Competitors: Sentry, PostHog, Bugsnag_

#### Developer Experience

2. **Source maps support**
   - Upload source maps for JavaScript/TypeScript
   - Deobfuscate minified stack traces
   - Link stack frames to original source code
   - Support for multiple source map formats
   - _Competitors: Sentry, Rollbar, Bugsnag, Raygun_

3. **SDK expansion** _(Python SDK and Django/FastAPI/Flask/DRF/Graphene/Logging integrations done — see [Completed](#8-official-python-sdk-)_
   - Official JavaScript/Node.js SDK
   - Official React SDK with error boundary
   - Framework integrations: Express, Next.js (JS)
   - _Competitors: All major platforms_

#### Integrations

4. **Slack/Discord notifications**
    - Webhook-based notifications to Slack channels
    - Discord webhook support
    - Configurable notification triggers (new issue, threshold breach, etc.)
    - Rich message formatting with error details
    - _Competitors: Sentry, Rollbar, Bugsnag, PostHog_

5. **GitHub/GitLab integration**
    - Create GitHub/GitLab issues from errors
    - Link errors to existing issues
    - Show commit info in error context
    - Suspect commit detection
    - _Competitors: Sentry, Rollbar, Bugsnag_

### Priority 2: Enhanced Functionality (Medium Impact)

#### Context & Debugging

6. ~~**Breadcrumbs**~~ ✅ _Done — see [Completed](#9-breadcrumbs-)_
    - _Remaining optional: JS SDK for automatic clicks/navigation/console in browser._

7. **User context & impact analysis**
    - Track affected user count per issue
    - User identification (email, ID, custom attributes)
    - "Crash-free users" metric
    - User session history
    - _Competitors: Sentry, Bugsnag, Raygun_

8. **Environment & release tracking**
    - Environment tags (production, staging, development)
    - Release/version tracking
    - Filter errors by environment and release
    - Release health metrics
    - First seen / last seen in release
    - _Competitors: Sentry, Rollbar, Bugsnag_

9. **Custom tags & attributes**
    - Add custom key-value tags to events
    - Filter and search by custom tags
    - Tag-based alerting rules
    - _Competitors: All major platforms_

#### Search & Filtering

10. **Advanced search & filtering**
    - Full-text search across error messages
    - Filter by: date range, level, environment, release, tags
    - Saved searches / filters
    - Search within stack traces
    - _Competitors: Sentry, Rollbar_

#### API & Webhooks

11. **Public REST API**
    - API for querying issues and events
    - API for managing projects and settings
    - API key authentication
    - Rate limiting
    - OpenAPI documentation
    - _Competitors: All major platforms_

12. **Outgoing webhooks**
    - Configurable webhooks for events (new issue, resolved, etc.)
    - Custom webhook payloads
    - Webhook retry logic
    - Webhook logs and debugging
    - _Competitors: Sentry, Rollbar_

#### Team Collaboration

13. **Team & organization management** _(partially done in v0.9.0)_
    - ~~Multiple users per project (project members)~~ ✅
    - ~~Invite users via email (team invites, accept/decline)~~ ✅
    - ~~Teams/Teams Pro plans with member limits~~ ✅
    - Remaining: role-based access (Owner, Admin, Member, Viewer), organization-level grouping, project-level permission roles
    - _Competitors: Sentry, Rollbar, Bugsnag_

14. **Comments & notes on issues**
    - Add comments to issues
    - @mention team members
    - Activity log / audit trail
    - _Competitors: Sentry, PostHog_

### Priority 3: Advanced Features (Future)

#### Performance & Monitoring

15. **Performance monitoring (APM)**
    - Transaction tracing
    - Latency percentiles (p50, p95, p99)
    - Slow transaction detection
    - Database query tracking
    - _Competitors: Sentry, Raygun, Bugsnag_

16. **Session replay**
    - Record and replay user sessions
    - Link replays to errors
    - Privacy controls (mask sensitive data)
    - DOM snapshots
    - _Competitors: Sentry, LogRocket, PostHog, Rollbar_

17. **Uptime monitoring**
    - HTTP endpoint monitoring
    - Uptime percentage tracking
    - Downtime alerts
    - Response time tracking
    - _Competitors: GlitchTip, Bugsnag_

#### Intelligence & Automation

18. **AI-powered root cause analysis**
    - Automated error analysis and suggestions
    - Similar error detection
    - Fix recommendations
    - _Competitors: Rollbar, Sentry (Seer)_

19. **Suspect deploy detection**
    - Automatically identify which deployment caused errors
    - Deployment timeline correlation
    - Auto-resolve on deploy option
    - _Competitors: Rollbar, Sentry_

20. **Smart alerting & anomaly detection**
    - Spike detection (unusual error rate)
    - Baseline comparison alerts
    - Alert fatigue reduction (digest mode)
    - _Competitors: Sentry, Rollbar_

#### Enterprise Features

21. **SAML/SSO authentication**
    - Single Sign-On support
    - SAML 2.0 integration
    - OIDC support
    - _Competitors: Sentry, Rollbar, Bugsnag (Enterprise)_

22. **Audit logs**
    - Track all user actions
    - Compliance reporting
    - Data export
    - _Competitors: Sentry, Rollbar (Enterprise)_

23. **Data retention policies**
    - Configurable retention periods
    - Auto-delete old events
    - Data export before deletion
    - _Competitors: All major platforms_

24. **On-premise / air-gapped deployment**
    - Full self-hosted deployment guide
    - Docker Compose production setup
    - Kubernetes Helm charts
    - Offline installation support
    - _Competitors: Sentry, GlitchTip, Bugsink_

#### Mobile & Platform Expansion

25. **Mobile SDKs**
    - iOS SDK (Swift)
    - Android SDK (Kotlin/Java)
    - React Native SDK
    - Flutter SDK
    - Crash symbolication
    - _Competitors: Sentry, Bugsnag, Rollbar_

26. **Real User Monitoring (RUM)**
    - Page load performance
    - Core Web Vitals
    - User satisfaction scores
    - Geographic performance breakdown
    - _Competitors: Raygun, LogRocket, Sentry_

---

## Feature Comparison Matrix

| Feature | XrayRadar | Sentry | Rollbar | Bugsnag | PostHog |
|---------|-----------|--------|---------|---------|---------|
| Error tracking | ✅ | ✅ | ✅ | ✅ | ✅ |
| Error grouping (fingerprinting) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Email alerts | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard statistics | ✅ | ✅ | ✅ | ✅ | ✅ |
| Usage limits by plan | ✅ | ✅ | ✅ | ✅ | ✅ |
| Email verification | ✅ | ✅ | ✅ | ✅ | ✅ |
| Password reset | ✅ | ✅ | ✅ | ✅ | ✅ |
| Issue status (resolve/ignore) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Issue assignment | ❌ | ✅ | ✅ | ✅ | ✅ |
| Source maps | ❌ | ✅ | ✅ | ✅ | ✅ |
| Multiple SDKs | ❌ | ✅ | ✅ | ✅ | ✅ |
| Slack integration | ❌ | ✅ | ✅ | ✅ | ✅ |
| GitHub integration | ❌ | ✅ | ✅ | ✅ | ❌ |
| Breadcrumbs | ✅ | ✅ | ✅ | ✅ | ❌ |
| User context | ❌ | ✅ | ✅ | ✅ | ✅ |
| Release tracking | ❌ | ✅ | ✅ | ✅ | ❌ |
| Custom tags | ❌ | ✅ | ✅ | ✅ | ✅ |
| Public API | ❌ | ✅ | ✅ | ✅ | ✅ |
| Webhooks | ❌ | ✅ | ✅ | ✅ | ✅ |
| Team management (plans, members, invites) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Performance monitoring | ❌ | ✅ | ❌ | ✅ | ❌ |
| Session replay | ❌ | ✅ | ✅ | ❌ | ✅ |
| AI analysis | ❌ | ✅ | ✅ | ❌ | ❌ |
| Mobile SDKs | ❌ | ✅ | ✅ | ✅ | ✅ |
| Self-hosted | ✅ | ✅ | ❌ | ❌ | ✅ |

---

## Recommended Implementation Order

Based on competitive analysis and user value:

### Phase 1: Core Workflow (v0.8.0)
1. ~~Issue status management~~ ✅
2. Issue assignment (#1)
3. Source maps support (#2)

### Phase 2: Team & Integrations (v0.9.0)
4. ~~Team & organization management (partial)~~ ✅ — project members, team invites, Teams/Teams Pro plans (#13)
5. Slack/Discord notifications (#4)
6. GitHub/GitLab integration (#5)
7. Custom tags & attributes (#9)

### Phase 3: Enhanced Context (v0.10.0)
8. Breadcrumbs (#6) ✅
9. User context & impact (#7)
10. Environment & release tracking (#8)

### Phase 4: Platform Expansion (v0.11.0)
11. Public REST API (#11)
12. Outgoing webhooks (#12)
13. JavaScript/Node.js SDK (#3)

### Phase 5: Collaboration (v0.12.0)
14. Team roles & organization (RBAC, project-level roles — remainder of #13)
15. Comments & notes (#14)
16. Advanced search & filtering (#10)

### Phase 6: Advanced (v1.0.0+)
16. Performance monitoring (#15)
17. Session replay (#16)
18. AI-powered analysis (#18)

---

## Notes

- Features are organized by priority and competitive importance
- Implementation order balances user value with development complexity
- Self-hosted deployment remains a key differentiator
- Focus on developer experience and workflow efficiency
- Consider community feedback when adjusting priorities
