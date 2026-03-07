# Rate limiting

## Overview

Public endpoints are rate limited to reduce abuse, brute force, and resource exhaustion. Two scopes are used: **IP-based** limits for auth endpoints (signup, login, forgot-password, etc.) and **token-based** limits for event ingestion. The implementation uses [slowapi](https://github.com/laurentS/slowapi) with an in-memory store; limits are configurable via environment variables. When a limit is exceeded, the server returns **429 Too Many Requests** with an error message.

## Scopes and keys

| Scope | Key function | Endpoints | Default limit |
|-------|--------------|-----------|----------------|
| Auth | `get_rate_limit_key_auth` (client IP) | signup, login, forgot-password, reset-password, verify-email, resend-verification | 5/minute |
| Signup | `get_rate_limit_key_auth` (client IP) | signup only (stacked with auth limit) | 10/hour |
| Event ingest | `get_rate_limit_key_token` (API token) | `POST /api/{project_id}/store/` | 100/minute |

- **Auth**: Key is the client IP. IP is taken from `X-Forwarded-For` (first value) when behind a proxy, otherwise from `request.client.host`; fallback `127.0.0.1`. Each IP has its own bucket; different IPs do not share the auth limit.
- **Event ingest**: Key is the value of the `X-Xrayradar-Token` header (or `"no-token"` if missing). Each token has its own bucket; different tokens do not share the ingest limit.

## Flow

```mermaid
sequenceDiagram
    participant Client
    participant Middleware
    participant Limiter
    participant Endpoint

    Client->>Middleware: Request
    Middleware->>Limiter: Check limit (key = IP or token)
    alt Within limit
        Limiter->>Endpoint: Proceed
        Endpoint->>Client: 200 (or other success)
    else Limit exceeded
        Limiter->>Client: 429 Too Many Requests
    end
```

1. Request hits a rate-limited route (auth or event ingest).
2. **SlowAPIMiddleware** runs before the route. The limiter computes the key using the route’s `key_func` (IP for auth, token for ingest).
3. slowapi checks the in-memory store for that key and window. If under the limit, the request proceeds; if over, slowapi raises `RateLimitExceeded`.
4. The **exception handler** (`_rate_limit_exceeded_handler`) converts that to a **429** response with a JSON body containing a “rate limit” message.
5. Rate limit response headers are **disabled** (`headers_enabled=False` on the limiter), so no `X-RateLimit-*` headers are sent.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `XRAYRADAR_RATE_LIMIT_AUTH` | Auth endpoints limit (e.g. `5/minute`, `10/hour`) | `5/minute` |
| `XRAYRADAR_RATE_LIMIT_SIGNUP` | Signup-only limit per IP (stacked with auth limit to reduce mass signup). Increase for shared-IP use (e.g. office, testing). | `10/hour` |
| `XRAYRADAR_RATE_LIMIT_EVENT_INGEST` | Event ingest limit per token | `100/minute` |

Format is `N/minute`, `N/hour`, or `N/day` (slowapi format).

## Key components

- **Limiter and key functions:** `src/xrayradar_server/rate_limit.py` — `limiter`, `get_client_ip`, `get_rate_limit_key_auth`, `get_rate_limit_key_token`
- **Constants:** `src/xrayradar_server/constants.py` — `RATE_LIMIT_AUTH`, `RATE_LIMIT_SIGNUP`, `RATE_LIMIT_EVENT_INGEST` (from env)
- **App wiring:** `src/xrayradar_server/main.py` — `app.state.limiter = limiter`, `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)`, `SlowAPIMiddleware`
- **Auth decorators:** `src/xrayradar_server/routers/user_auth.py` — `@limiter.limit(RATE_LIMIT_AUTH, key_func=get_rate_limit_key_auth)` on login, forgot-password, reset-password, verify-email, resend-verification; signup additionally has `@limiter.limit(RATE_LIMIT_SIGNUP, ...)` so both limits apply (stricter cap on new accounts per IP)
- **Event ingest decorator:** `src/xrayradar_server/routers/api.py` — `@limiter.limit(RATE_LIMIT_EVENT_INGEST, key_func=get_rate_limit_key_token)` on `store_event`

## Endpoints covered

| Method | Path | Key | Limit |
|--------|------|-----|--------|
| GET | `/auth/signup-status` | IP | RATE_LIMIT_AUTH |
| POST | `/auth/signup` | IP | RATE_LIMIT_AUTH + RATE_LIMIT_SIGNUP (both must pass) |
| POST | `/auth/login` | IP | RATE_LIMIT_AUTH |
| POST | `/auth/forgot-password` | IP | RATE_LIMIT_AUTH |
| POST | `/auth/reset-password` | IP | RATE_LIMIT_AUTH |
| GET | `/auth/verify-email` | IP | RATE_LIMIT_AUTH |
| POST | `/auth/resend-verification` | IP | RATE_LIMIT_AUTH |
| POST | `/api/{project_id}/store/` | Token | RATE_LIMIT_EVENT_INGEST |

`/auth/logout` and `/api/me` are **not** rate limited (logout is low-risk; `/api/me` is protected by session and not public).

## Storage and deployment

- **Storage:** slowapi’s default in-memory backend. Counters are per-process; they are not shared across multiple worker processes or instances.
- **Multi-worker / multi-instance:** Each process has its own buckets. With N workers, effective capacity per key is roughly N× the configured limit (e.g. 5/min per worker → 5N/min total for that key). For stricter global limits, use a shared store (e.g. Redis) via slowapi’s storage backend if supported, or put a reverse proxy / API gateway in front with its own rate limiting.

## Testing

- **Tests:** `tests/test_00_rate_limit.py` — auth 429 when exceeding limit, separate buckets per IP, signup/login/forgot-password limits, event ingest 429 per token, separate buckets per token, 429 response body contains “rate limit”, `get_client_ip` fallback.

## Relation to other features

- **Usage limiting** (see [usage-limiting.md](usage-limiting.md)): Plan-tier event caps (e.g. 1,000 for Free) are enforced **after** rate limiting. Rate limiting caps requests per minute; usage limiting caps total stored events per user.
- **Auth** (see [auth.md](auth.md)): Rate limiting on auth endpoints mitigates brute force and credential stuffing; it does not replace strong passwords or optional 2FA.

## Signup brute-force and mass registration

Signup is a common target for brute force (mass account creation, enumeration). Mitigations in place:

1. **Stricter signup limit** — In addition to the general auth limit (e.g. 5/minute), signup has a per-IP limit (default **10/hour**) via `XRAYRADAR_RATE_LIMIT_SIGNUP`. Both limits must pass. For shared-IP scenarios (e.g. office, testing), set a higher value (e.g. `20/hour` or `50/day`).
2. **IP-based key** — Same as other auth; attackers need many IPs to scale.
3. **Email verification** — New accounts are unverified until the user clicks the link; sensitive actions can require a verified user (`require_verified_user`).
4. **Admin notification** — Admins receive an email on each new signup (see [auth](auth.md#signup-email-job-data-flow)) so abuse can be spotted.
5. **Global daily cap** — `XRAYRADAR_MAX_SIGNUPS_PER_DAY` limits total signups in a rolling 24-hour window across all IPs. Default **100**; set to `0` for no limit. When exceeded, signup returns **503** with "Daily signup limit reached. Please try again later."

Optional hardening not implemented: CAPTCHA (e.g. reCAPTCHA, Cloudflare Turnstile) on the signup form, or a shared rate-limit store (e.g. Redis) across workers for stricter global caps.

## Multiple accounts from the same IP

Legitimate cases (shared office, testing, agencies) may need several signups from one IP. Configure a higher signup limit via **`XRAYRADAR_RATE_LIMIT_SIGNUP`** so the per-IP cap is less strict, for example:

- `20/hour` — e.g. small office
- `50/day` — e.g. dev/staging with many test accounts

The general auth limit (`XRAYRADAR_RATE_LIMIT_AUTH`, default 5/minute) still applies, so each IP is still limited in requests per minute; only the extra signup cap is relaxed.
