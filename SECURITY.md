# Security Audit Report

This document outlines the security practices and audit results for `xrayradar` Python SDK.

## Automated Security Scanning

The repository uses automated security scanning in CI/CD:

### Python SDK
- **Bandit**: Static security analysis for Python code
- **pip-audit**: Dependency vulnerability scanning

### Running Security Audits Locally

```bash
# Run comprehensive security audit
./scripts/security_audit.sh

# Or run individually:
# Backend static analysis
bandit -r src -q

# Backend dependency audit
pip-audit

# Or install dev dependencies and run:
pip install -e .[dev]
bandit -r src -q
pip-audit
```

## Security Best Practices Implemented

### 1. Secrets Management
- ✅ **No Hardcoded Secrets**: All sensitive values (DSN, auth tokens) come from environment variables or constructor parameters
- ✅ **DSN Redaction**: DSN secrets are automatically redacted in error messages (see `transport.py::_redact_dsn()`)
- ✅ **Token Handling**: Authentication tokens are read from environment variables (`XRAYRADAR_AUTH_TOKEN`) or passed securely via constructor
- ✅ **Secure Random**: Uses `secrets.SystemRandom()` for cryptographically secure random number generation (sampling)

### 2. Data Protection & Privacy
- ✅ **PII Protection**: Privacy-first defaults - PII is not sent unless explicitly enabled (`send_default_pii=True` or `XRAYRADAR_SEND_DEFAULT_PII=true`)
- ✅ **Header Filtering**: Sensitive headers are automatically filtered from request context:
  - `Authorization`
  - `Cookie`
  - `Set-Cookie`
  - `X-Api-Key`
  - `X-Forwarded-Authorization`
- ✅ **Error Message Safety**: Transport error messages avoid leaking large server response bodies (truncated to 200 characters)
- ✅ **Payload Size Limits**: Maximum payload size enforced (default 100KB) with automatic truncation

### 3. Input Validation
- ✅ **DSN Validation**: DSN format is validated with clear error messages
- ✅ **Configuration Validation**: All configuration values are validated:
  - `sample_rate` must be between 0.0 and 1.0
  - `max_breadcrumbs` must be non-negative
  - `timeout` must be positive
  - `max_payload_size` must be positive
- ✅ **Type Safety**: Uses type hints throughout the codebase

### 4. Transport Security
- ✅ **HTTPS Support**: Supports HTTPS connections with SSL verification (configurable via `verify_ssl`)
- ✅ **Timeout Protection**: HTTP requests have configurable timeouts (default 10 seconds) to prevent hanging
- ✅ **Rate Limiting Handling**: Properly handles HTTP 429 (rate limiting) responses with retry-after information
- ✅ **Error Handling**: Comprehensive error handling for network failures, encoding errors, and server errors

### 5. Framework Integration Security
- ✅ **Flask Integration**: Safely extracts request context without exposing sensitive headers
- ✅ **Django Integration**: Secure middleware that filters sensitive data from request context
- ✅ **FastAPI Integration**: Proper exception handling with request context filtering
- ✅ **Logging Integration**: Secure logging handler that doesn't leak sensitive information

### 6. Dependency Security
- ✅ **Regular Audits**: Dependencies scanned for known vulnerabilities in CI
- ✅ **Minimal Dependencies**: Core SDK has minimal dependencies (`requests`, `python-json-logger`)
- ✅ **Optional Dependencies**: Framework integrations are optional dependencies, reducing attack surface
- ✅ **Version Constraints**: Dependencies use version constraints to prevent unexpected updates

### 7. Code Quality
- ✅ **Type Hints**: Comprehensive type hints for better code safety
- ✅ **Error Messages**: Clear, actionable error messages that don't leak sensitive information
- ✅ **Exception Handling**: Proper exception handling with context preservation

## Security Audit Results

### Bandit Static Analysis

**Status**: ✅ **PASSED** (No security issues found)

Bandit scan completed with no security vulnerabilities detected. The codebase follows security best practices:
- No hardcoded secrets or passwords
- Proper use of secure random number generation
- Safe string handling
- No SQL injection risks (no direct database access)

### pip-audit Dependency Scanning

**Status**: ✅ **RUNS IN CI**

Dependencies are automatically scanned in CI for known vulnerabilities. To run locally:
```bash
pip-audit
```

**Note**: `pip-audit` may report that `xrayradar` itself cannot be audited because it's not published on PyPI during development. This is expected - the project code itself doesn't need vulnerability scanning, only its dependencies do.

## Known Security Considerations

### 1. SSL Certificate Verification
- **Status**: SSL verification is enabled by default (`verify_ssl=True`)
- **Impact**: Prevents man-in-the-middle attacks
- **Recommendation**: Keep SSL verification enabled in production. Only disable for testing with self-signed certificates

### 2. Payload Size Limits
- **Status**: Maximum payload size enforced (default 100KB)
- **Impact**: Prevents memory exhaustion from large events
- **Recommendation**: Adjust `max_payload_size` based on your needs, but keep reasonable limits

### 3. Sample Rate
- **Status**: Configurable sampling (default 1.0 = 100%)
- **Impact**: Can reduce event volume and costs
- **Recommendation**: Use appropriate sample rates for high-volume applications

### 4. Error Message Information Leakage
- **Status**: Error messages are designed to be helpful without leaking sensitive data
- **Impact**: DSN secrets are redacted, server responses are truncated
- **Recommendation**: Review error messages in production to ensure no sensitive data is exposed

### 5. Authentication Token Storage
- **Status**: Tokens are stored in memory and sent via HTTP headers
- **Impact**: Tokens in environment variables are secure; tokens in code are not recommended
- **Recommendation**: Always use environment variables (`XRAYRADAR_AUTH_TOKEN`) for authentication tokens

### 6. Network Security
- **Status**: SDK makes outbound HTTPS requests to XrayRadar servers
- **Impact**: Network traffic is encrypted
- **Recommendation**: Ensure network policies allow outbound connections to XrayRadar servers

## Security Checklist for Integration

Before integrating the SDK in production:

- [ ] Set `XRAYRADAR_AUTH_TOKEN` via environment variable (never hardcode)
- [ ] Verify DSN is correct and points to trusted XrayRadar server
- [ ] Enable SSL verification (`verify_ssl=True` in production)
- [ ] Review and configure `send_default_pii` based on privacy requirements
- [ ] Set appropriate `sample_rate` for your application volume
- [ ] Configure `max_payload_size` based on your needs
- [ ] Review dependencies regularly (`pip-audit`)
- [ ] Ensure network policies allow outbound HTTPS to XrayRadar servers
- [ ] Test error handling to ensure no sensitive data leaks in error messages
- [ ] Review framework integration settings (Flask/Django/FastAPI) for security

## Security Best Practices for Users

### 1. Environment Variables
Always use environment variables for sensitive configuration:
```bash
export XRAYRADAR_DSN="https://xrayradar.com/your_project_id"
export XRAYRADAR_AUTH_TOKEN="your_token_here"
```

### 2. PII Handling
Be mindful of PII when using `send_default_pii=True`:
- Review what data is being sent
- Ensure compliance with privacy regulations (GDPR, CCPA, etc.)
- Use tags and extra context instead of PII when possible

### 3. Error Context
Be careful with custom context data:
- Don't include sensitive data in `set_extra()` or `set_tag()`
- Review breadcrumbs to ensure no sensitive information is captured
- Use before_send hooks to filter sensitive data if needed

### 4. Framework Integration
When using framework integrations:
- Ensure proper request context filtering is working
- Review what headers and data are being captured
- Test with real requests to verify no sensitive data leaks

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email security concerns to: dev@xrayradar.com
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before public disclosure

## Security Updates

This document is updated as security practices evolve. Last updated: 2026-01-25
