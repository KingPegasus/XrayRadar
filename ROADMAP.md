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

### Usage & Limits

6. **Usage limiting for events stored per basic or free account** ✅
   - Implement event storage limits for free/basic tiers
   - Track event count per account (all event levels: error, warning, info, debug)
   - Enforce limits and notify users when approaching limits

### Context & Debugging

7. **Breadcrumbs** ✅
   - Capture trail of events leading to error (SDK buffer → payload → storage)
   - Automatic breadcrumbs: **HTTP/network requests** via Django/FastAPI/Flask middleware (one breadcrumb per request)
   - Custom breadcrumbs via SDK: `add_breadcrumb()`, `clear_breadcrumbs()`, `max_breadcrumbs` config
   - Breadcrumb timeline in **event** detail view (BreadcrumbTimeline: type icons, level colors, relative time, expandable data, sort toggle)
   - _Note: Automatic clicks, navigation, and console logs would require a JavaScript SDK (not yet implemented); Python SDK supports manual breadcrumbs for any type._

---

## Pending Features

_Features that are planned for upcoming releases, organized by priority._

### Priority 1: Core Functionality (High Impact)

#### Issue Management & Workflow

1. **Issue status management**
   - Mark issues as: Open, In Progress, Resolved, Ignored/Muted
   - Auto-reopen issues on new occurrence after resolution
   - "Resolved until next release" option
   - Bulk actions (resolve multiple, ignore multiple)
   - _Competitors: Sentry, Rollbar, Bugsnag, PostHog_

2. **Issue assignment**
   - Assign issues to team members
   - Auto-assignment rules based on file path, error type, or project
   - Team/role-based assignment
   - Assignment notifications
   - _Competitors: Sentry, PostHog, Bugsnag_

#### Developer Experience

3. **Source maps support**
   - Upload source maps for JavaScript/TypeScript
   - Deobfuscate minified stack traces
   - Link stack frames to original source code
   - Support for multiple source map formats
   - _Competitors: Sentry, Rollbar, Bugsnag, Raygun_

4. **SDK expansion**
   - Official Python SDK (beyond basic HTTP)
   - Official JavaScript/Node.js SDK
   - Official React SDK with error boundary
   - Framework integrations (Django, FastAPI, Express, Next.js)
   - _Competitors: All major platforms_

#### Integrations

5. **Slack/Discord notifications**
    - Webhook-based notifications to Slack channels
    - Discord webhook support
    - Configurable notification triggers (new issue, threshold breach, etc.)
    - Rich message formatting with error details
    - _Competitors: Sentry, Rollbar, Bugsnag, PostHog_

6. **GitHub/GitLab integration**
    - Create GitHub/GitLab issues from errors
    - Link errors to existing issues
    - Show commit info in error context
    - Suspect commit detection
    - _Competitors: Sentry, Rollbar, Bugsnag_

### Priority 2: Enhanced Functionality (Medium Impact)

#### Context & Debugging

7. ~~**Breadcrumbs**~~ ✅ _Done — see [Completed](#7-breadcrumbs-)_
    - _Remaining optional: JS SDK for automatic clicks/navigation/console in browser._

8. **User context & impact analysis**
    - Track affected user count per issue
    - User identification (email, ID, custom attributes)
    - "Crash-free users" metric
    - User session history
    - _Competitors: Sentry, Bugsnag, Raygun_

9. **Environment & release tracking**
    - Environment tags (production, staging, development)
    - Release/version tracking
    - Filter errors by environment and release
    - Release health metrics
    - First seen / last seen in release
    - _Competitors: Sentry, Rollbar, Bugsnag_

10. **Custom tags & attributes**
    - Add custom key-value tags to events
    - Filter and search by custom tags
    - Tag-based alerting rules
    - _Competitors: All major platforms_

#### Search & Filtering

11. **Advanced search & filtering**
    - Full-text search across error messages
    - Filter by: date range, level, environment, release, tags
    - Saved searches / filters
    - Search within stack traces
    - _Competitors: Sentry, Rollbar_

#### API & Webhooks

12. **Public REST API**
    - API for querying issues and events
    - API for managing projects and settings
    - API key authentication
    - Rate limiting
    - OpenAPI documentation
    - _Competitors: All major platforms_

13. **Outgoing webhooks**
    - Configurable webhooks for events (new issue, resolved, etc.)
    - Custom webhook payloads
    - Webhook retry logic
    - Webhook logs and debugging
    - _Competitors: Sentry, Rollbar_

#### Team Collaboration

14. **Team & organization management**
    - Multiple users per organization
    - Role-based access (Owner, Admin, Member, Viewer)
    - Project-level permissions
    - Invite users via email
    - _Competitors: Sentry, Rollbar, Bugsnag_

15. **Comments & notes on issues**
    - Add comments to issues
    - @mention team members
    - Activity log / audit trail
    - _Competitors: Sentry, PostHog_

### Priority 3: Advanced Features (Future)

#### Performance & Monitoring

16. **Performance monitoring (APM)**
    - Transaction tracing
    - Latency percentiles (p50, p95, p99)
    - Slow transaction detection
    - Database query tracking
    - _Competitors: Sentry, Raygun, Bugsnag_

17. **Session replay**
    - Record and replay user sessions
    - Link replays to errors
    - Privacy controls (mask sensitive data)
    - DOM snapshots
    - _Competitors: Sentry, LogRocket, PostHog, Rollbar_

18. **Uptime monitoring**
    - HTTP endpoint monitoring
    - Uptime percentage tracking
    - Downtime alerts
    - Response time tracking
    - _Competitors: GlitchTip, Bugsnag_

#### Intelligence & Automation

19. **AI-powered root cause analysis**
    - Automated error analysis and suggestions
    - Similar error detection
    - Fix recommendations
    - _Competitors: Rollbar, Sentry (Seer)_

20. **Suspect deploy detection**
    - Automatically identify which deployment caused errors
    - Deployment timeline correlation
    - Auto-resolve on deploy option
    - _Competitors: Rollbar, Sentry_

21. **Smart alerting & anomaly detection**
    - Spike detection (unusual error rate)
    - Baseline comparison alerts
    - Alert fatigue reduction (digest mode)
    - _Competitors: Sentry, Rollbar_

#### Enterprise Features

22. **SAML/SSO authentication**
    - Single Sign-On support
    - SAML 2.0 integration
    - OIDC support
    - _Competitors: Sentry, Rollbar, Bugsnag (Enterprise)_

23. **Audit logs**
    - Track all user actions
    - Compliance reporting
    - Data export
    - _Competitors: Sentry, Rollbar (Enterprise)_

24. **Data retention policies**
    - Configurable retention periods
    - Auto-delete old events
    - Data export before deletion
    - _Competitors: All major platforms_

25. **On-premise / air-gapped deployment**
    - Full self-hosted deployment guide
    - Docker Compose production setup
    - Kubernetes Helm charts
    - Offline installation support
    - _Competitors: Sentry, GlitchTip, Bugsink_

#### Mobile & Platform Expansion

26. **Mobile SDKs**
    - iOS SDK (Swift)
    - Android SDK (Kotlin/Java)
    - React Native SDK
    - Flutter SDK
    - Crash symbolication
    - _Competitors: Sentry, Bugsnag, Rollbar_

27. **Real User Monitoring (RUM)**
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
| Issue status (resolve/ignore) | ❌ | ✅ | ✅ | ✅ | ✅ |
| Issue assignment | ❌ | ✅ | ✅ | ✅ | ✅ |
| Source maps | ❌ | ✅ | ✅ | ✅ | ✅ |
| Multiple SDKs | ❌ | ✅ | ✅ | ✅ | ✅ |
| Slack integration | ❌ | ✅ | ✅ | ✅ | ✅ |
| GitHub integration | ❌ | ✅ | ✅ | ✅ | ❌ |
| Breadcrumbs | ❌ | ✅ | ✅ | ✅ | ❌ |
| User context | ❌ | ✅ | ✅ | ✅ | ✅ |
| Release tracking | ❌ | ✅ | ✅ | ✅ | ❌ |
| Custom tags | ❌ | ✅ | ✅ | ✅ | ✅ |
| Public API | ❌ | ✅ | ✅ | ✅ | ✅ |
| Webhooks | ❌ | ✅ | ✅ | ✅ | ✅ |
| Team management | ❌ | ✅ | ✅ | ✅ | ✅ |
| Performance monitoring | ❌ | ✅ | ❌ | ✅ | ❌ |
| Session replay | ❌ | ✅ | ✅ | ❌ | ✅ |
| AI analysis | ❌ | ✅ | ✅ | ❌ | ❌ |
| Mobile SDKs | ❌ | ✅ | ✅ | ✅ | ✅ |
| Self-hosted | ✅ | ✅ | ❌ | ❌ | ✅ |

---

## Recommended Implementation Order

Based on competitive analysis and user value:

### Phase 1: Core Workflow (v0.8.0)
1. Issue status management (#6)
2. Issue assignment (#7)
3. Source maps support (#8)

### Phase 2: Integrations (v0.9.0)
4. Slack/Discord notifications (#10)
5. GitHub/GitLab integration (#11)
6. Custom tags & attributes (#15)

### Phase 3: Enhanced Context (v0.10.0)
7. Breadcrumbs (#12)
8. User context & impact (#13)
9. Environment & release tracking (#14)

### Phase 4: Platform Expansion (v0.11.0)
10. Public REST API (#17)
11. Outgoing webhooks (#18)
12. JavaScript/Node.js SDK (#9)

### Phase 5: Collaboration (v0.12.0)
13. Team & organization management (#19)
14. Comments & notes (#20)
15. Advanced search & filtering (#16)

### Phase 6: Advanced (v1.0.0+)
16. Performance monitoring (#21)
17. Session replay (#22)
18. AI-powered analysis (#24)

---

## Notes

- Features are organized by priority and competitive importance
- Implementation order balances user value with development complexity
- Self-hosted deployment remains a key differentiator
- Focus on developer experience and workflow efficiency
- Consider community feedback when adjusting priorities
