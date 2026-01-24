# Security Audit Report

This document outlines the security practices and audit results for `xrayradar-server`.

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
- **Expected Warning**: `pip-audit` may report that `xrayradar-server` itself cannot be audited because it's not published on PyPI. This is expected and harmless - the project code itself doesn't need vulnerability scanning, only its dependencies do.
- **Local Packages**: If you see "Dependency not found on PyPI" for `xrayradar-server`, this is normal for local/private projects.

## Known Security Considerations

### 1. CORS Configuration
- **Status**: No CORS middleware configured
- **Impact**: API is same-origin only (intended for backend-frontend co-hosting)
- **Recommendation**: If API needs to be accessed from different origins, configure CORS appropriately

### 2. Rate Limiting
- **Status**: No rate limiting implemented
- **Impact**: Vulnerable to brute force attacks on login/signup endpoints
- **Recommendation**: Consider adding rate limiting middleware (e.g., `slowapi`)

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
- [ ] Configure rate limiting for public endpoints
- [ ] Set up monitoring and alerting for security events
- [ ] Regular security audits (run `./scripts/security_audit.sh`)

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email security concerns to the maintainers
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## Security Updates

This document is updated as security practices evolve. Last updated: 2026-01-23
