# Security Audit Report

This document outlines the security practices and audit results for **XrayRadar**

## Automated Security Scanning

The repository uses automated security scanning in CI/CD:

### Backend (Python)
- **Bandit**: Static security analysis for Python code
- **pip-audit**: Dependency vulnerability scanning

### Frontend (JavaScript/React)
- **npm audit**: Dependency vulnerability scanning

### Running Security Audits Locally

```bash
# Run comprehensive security audit
./scripts/security_audit.sh

# Or run individually:
# Backend static analysis
uv run bandit -r src

# Backend dependency audit
uv run pip-audit

# Frontend dependency audit
cd xrayradar-web && npm audit
```

## Security Best Practices Implemented

### 1. Authentication & Authorization
- ✅ **Password Hashing**: All passwords are hashed using secure hashing algorithms (see `auth.py`)
- ✅ **Session Management**: Secure session cookies with:
  - `httponly=True` (prevents XSS access)
  - `samesite="lax"` (CSRF protection)
  - `secure=True` in production (HTTPS only)
- ✅ **Token-Based Auth**: API tokens generated using `secrets.token_urlsafe()` (cryptographically secure)
- ✅ **OAuth State Validation**: GitHub OAuth flow includes state validation to prevent CSRF attacks
- ✅ **Admin Allowlist**: Admin access restricted to configured email allowlist

### 2. Input Validation
- ✅ **Pydantic Models**: All API inputs validated using Pydantic schemas
- ✅ **Email Validation**: Email format validation on signup/login
- ✅ **Password Requirements**: Minimum password length enforced (8 characters)
- ✅ **SQL Injection Protection**: All database queries use SQLAlchemy ORM (parameterized queries)

### 3. Data Protection
- ✅ **Secrets Management**: No hardcoded secrets; all sensitive values from environment variables
- ✅ **Token Storage**: Tokens stored securely in database; never logged or exposed unnecessarily
- ✅ **Cookie Security**: Session cookies use secure flags and appropriate expiration

### 4. API Security
- ✅ **Token Revocation**: Tokens can be revoked and are checked on every request
- ✅ **Project Access Control**: Fine-grained access control per token per project
- ✅ **Error Messages**: Generic error messages to prevent information leakage

### 5. Dependency Security
- ✅ **Regular Audits**: Dependencies scanned for known vulnerabilities in CI
- ✅ **Pinned Versions**: Dependencies use version constraints to prevent unexpected updates

### 6. pip-audit Notes
- **Expected Warning**: `pip-audit` may report that the local package name `xrayradar-server` (from `pyproject.toml`) cannot be audited because it is not published on PyPI. This is expected and harmless: only dependencies need vulnerability scanning, not the application package entry itself.
- **Local Packages**: If you see "Dependency not found on PyPI" for `xrayradar-server`, this is normal for a project installed from a checkout.
- **Use the project environment**: Run audits after `uv sync --extra dev` so `uv run pip-audit` uses this repo’s `.venv` (and the dev extra includes `pip-audit` + `pip`). If you see a warning about auditing a different Python than your venv, set `PIPAPI_PYTHON_LOCATION` to your `.venv/bin/python` (see [pip-audit](https://github.com/pypa/pip-audit) / pip-api docs).

## Known Security Considerations

### 1. CORS Configuration
- **Status**: CORS middleware enabled for event ingest from browser apps
- **Details**: `allow_origins=["*"]`, `allow_methods=["GET", "POST", "OPTIONS"]`, `allow_headers=["*"]`, `allow_credentials=False`. This allows React and other frontends on any origin to `POST` to `/api/{project_id}/store/`; auth is by `X-Xrayradar-Token` only.

### 2. Rate Limiting
- **Status**: Implemented (slowapi)
- **Details**: Public endpoints are rate limited. Auth endpoints (signup, login, forgot-password, reset-password, verify-email, resend-verification) are limited per client IP. Event ingestion (`POST /api/{project_id}/store/`) is limited per API token. Limits are configurable via `XRAYRADAR_RATE_LIMIT_AUTH` (default: 5/minute) and `XRAYRADAR_RATE_LIMIT_EVENT_INGEST` (default: 100/minute). When exceeded, the server returns 429 Too Many Requests.

### 3. Bandit Findings
The following low-severity findings are expected and safe:
- `B106` (hardcoded_password_funcarg): Empty token string for session-admin (intentional, not a secret)
- `B105` (hardcoded_password_string): GitHub OAuth URL (not a password, marked with `# nosec`)

### 4. Session Expiration
- Admin sessions: 12 hours
- User sessions: 30 days
- **Recommendation**: Consider shorter session expiration for admin sessions

## Security Checklist for Deployment

Before deploying to production:

- [ ] Set `XRAYRADAR_SESSION_SECRET` to a strong random value
- [ ] Configure `XRAYRADAR_ADMIN_EMAILS` with authorized admin emails
- [ ] Use HTTPS (set `XRAYRADAR_ENV=production` or ensure `cookie_secure()` returns `True`)
- [ ] Review and update dependencies regularly (`pip-audit`, `npm audit`)
- [ ] Configure database with strong credentials
- [ ] Enable database connection encryption (SSL/TLS)
- [ ] Set up proper firewall rules
- [x] Configure rate limiting for public endpoints (defaults: 5/min auth per IP, 100/min event ingest per token)
- [ ] Set up monitoring and alerting for security events
- [ ] Regular security audits (run `./scripts/security_audit.sh`)

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email security concerns to the maintainers
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## Security Updates

This document is updated as security practices evolve. Last updated: 2026-03-28
