# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-25

### Added
- Python Logging Integration: New `LoggingIntegration` class and `setup_logging()` function to automatically capture log messages from Python's `logging` module
  - Configurable log level filtering (default: WARNING and above)
  - Logger name prefix filtering
  - Logger exclusion support
  - Automatic mapping of Python logging levels to XrayRadar levels
  - Exception capture from log records with `exc_info`
- Enhanced error messages with context and actionable guidance:
  - DSN parsing errors now include expected format examples
  - HTTP status code errors include specific troubleshooting steps
  - Configuration validation errors include expected value ranges
- Comprehensive test coverage for logging integration (26 test cases)
- Example usage file: `examples/logging_example.py`
- Logging integration section in README with usage examples
- Improved exception documentation with examples

### Changed
- Improved error messages in `TransportError`, `InvalidDsnError`, and `ConfigurationError` exceptions
- Enhanced HTTP transport error messages with status-code-specific guidance (401, 403, 404, 500+)

## [0.2.0] - 2026-01-18

### Added
- Graphene Integration: Support for GraphQL error tracking via Graphene
  - `GrapheneIntegration` class for automatic exception capture in GraphQL resolvers
  - Middleware support for GraphQL views
- Django REST Framework (DRF) Integration: Support for DRF exception handling
  - `make_drf_exception_handler()` function to wrap DRF exception handlers
  - Automatic error reporting for DRF API exceptions
- Comprehensive test coverage for Graphene and DRF integrations (2 test cases for Graphene, 5 test cases for DRF)
- Integration examples and usage documentation in README for both Graphene and DRF integrations

## [0.1.0] - 2026-01-13

### Added
- Initial public release: Production-ready Python error tracking SDK for XrayRadar
- `ErrorTracker` client with DSN-based configuration
- Exception capture with stack traces, fingerprints, breadcrumbs, tags, and extra context
- Environment variable configuration support:
  - `XRAYRADAR_DSN`: Data Source Name
  - `XRAYRADAR_ENVIRONMENT`: Environment name (development, staging, production)
  - `XRAYRADAR_RELEASE`: Release version
  - `XRAYRADAR_SAMPLE_RATE`: Sampling rate (0.0 to 1.0)
  - `XRAYRADAR_SEND_DEFAULT_PII`: Enable/disable PII collection
  - `XRAYRADAR_AUTH_TOKEN`: Authentication token (required)
- Privacy-first defaults: PII is not sent unless explicitly enabled (`send_default_pii=True` or `XRAYRADAR_SEND_DEFAULT_PII=true`)
- Automatic filtering of sensitive headers (`Authorization`, `Cookie`, `Set-Cookie`, `X-Api-Key`, `X-Forwarded-Authorization`)
- DSN secrets redaction in error messages
- Transport error messages that avoid leaking large server response bodies
- Flask Integration: `FlaskIntegration` class with automatic exception capture, request context handling, breadcrumb collection, and safe header filtering
- Django Integration: `DjangoIntegration` class with middleware support, automatic exception capture, request context handling, and Django settings integration
- FastAPI Integration: `FastAPIIntegration` class with exception handlers, middleware support, and request validation error handling
- CI test workflow with Python version matrix (3.8, 3.9, 3.10, 3.11, 3.12, 3.13)
- Security scanning in CI with `bandit` for static security analysis and `pip-audit` for dependency vulnerability scanning
- PyPI publishing workflow via GitHub Actions with Trusted Publishing / OIDC-ready PyPI environment and automated version management


[0.3.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/KingPegasus/XrayRadar/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/KingPegasus/XrayRadar/releases/tag/v0.1.0
