# XrayRadar Python SDK

[![PyPI version](https://img.shields.io/pypi/v/xrayradar?style=flat-square)](https://pypi.org/project/xrayradar/)
![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square)
[![CI](https://img.shields.io/github/actions/workflow/status/KingPegasus/XrayRadar/ci.yml?label=CI&style=flat-square)](https://github.com/KingPegasus/XrayRadar/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?style=flat-square)](https://kingpegasus.github.io/XrayRadar/)

**Official Python SDK for XrayRadar** — Capture, track, and monitor errors in your Python applications with ease.

XrayRadar is a powerful error tracking and monitoring platform that helps you identify, debug, and resolve issues in your applications. This SDK provides seamless integration with XrayRadar's error tracking service, enabling automatic exception capture, rich context collection, and real-time error monitoring.

## Features

- **Automatic Exception Capture**: Automatically captures uncaught exceptions from your application
- **Manual Error Reporting**: Capture exceptions and messages manually with full control
- **Rich Context**: Collects breadcrumbs, tags, user data, and custom context for better debugging
- **Framework Integrations**: Built-in integrations for Flask, Django, FastAPI, Graphene (GraphQL), and Django REST Framework (DRF)
- **Flexible Transport**: HTTP transport with retry logic and rate limiting for reliable delivery
- **Sampling**: Configurable sampling to reduce noise and control event volume
- **Privacy-First**: Default PII protection with opt-in for sensitive data
- **Debug Mode**: Console output for development and testing
- **Configuration**: Environment variables and file-based configuration for flexible setup

## Prerequisites

Before using the XrayRadar Python SDK, you need to:

1. **Sign up for XrayRadar**: Create an account at [XrayRadar](https://xrayradar.com)
2. **Create a Project**: After signing up, create a new project in your XrayRadar dashboard
3. **Get Your DSN**: Copy your project's DSN (Data Source Name) from the project settings. The DSN format is: `https://xrayradar.com/your_project_id`
4. **Get Your Token**: Obtain your authentication token from your project settings. This token is required for authenticating requests to the XrayRadar server

Once you have your DSN and token, you're ready to integrate the SDK into your application.

## Installation

```bash
pip install xrayradar
```

### Optional dependencies for framework integrations:

```bash
# For Flask
pip install xrayradar[flask]

# For Django
pip install xrayradar[django]

# For FastAPI
pip install xrayradar[fastapi]

# For development
pip install xrayradar[dev]
```

## Quick Start

### Basic Usage

```python
import xrayradar
from xrayradar import ErrorTracker

# Initialize the SDK with your XrayRadar DSN
# Replace with your actual DSN from your XrayRadar project settings
tracker = ErrorTracker(
    dsn="https://xrayradar.com/your_project_id",  # Your XrayRadar DSN
    environment="production",
    release="1.0.0",
)

# Privacy-first by default (recommended)
# The SDK avoids sending default PII (IP address, query strings, auth/cookie headers).
# If you want to send default PII, explicitly opt in:
# tracker = ErrorTracker(dsn="...", send_default_pii=True)

# Capture an exception
try:
    1 / 0
except Exception as e:
    tracker.capture_exception(e)

# Or use the global client (recommended for simple applications)
xrayradar.init(
    dsn="https://xrayradar.com/your_project_id",  # Your XrayRadar DSN
    environment="production",
)

try:
    1 / 0
except Exception:
    xrayradar.capture_exception()
```

### Environment Variables

You can configure the SDK using environment variables. This is especially useful for deployment and different environments:

```bash
# Required: Your XrayRadar project DSN
export XRAYRADAR_DSN="https://xrayradar.com/your_project_id"

# Required: Authentication token for XrayRadar
export XRAYRADAR_AUTH_TOKEN="your_token"

# Optional: Environment and release information
export XRAYRADAR_ENVIRONMENT="production"
export XRAYRADAR_RELEASE="1.0.0"

# Optional: Sampling and privacy settings
export XRAYRADAR_SAMPLE_RATE="0.5"  # Send 50% of events (0.0 to 1.0)
export XRAYRADAR_SEND_DEFAULT_PII="false"  # Privacy-first by default

```

### Authentication

XrayRadar requires authentication to ensure secure error reporting. The SDK automatically sends your authentication token in the request header:

- Header: `X-Xrayradar-Token: <your_token>`

You can provide your authentication token in two ways:

**Option 1: Environment Variable** (Recommended for production)

```bash
export XRAYRADAR_AUTH_TOKEN="your_token_here"
```

**Option 2: Explicit Configuration**

```python
from xrayradar import ErrorTracker

tracker = ErrorTracker(
    dsn="https://xrayradar.com/your_project_id",
    auth_token="your_token_here",
)
```

> **Note**: Your authentication token can be found in your XrayRadar project settings. Keep your token secure and never commit it to version control.

## Privacy

By default, `xrayradar` is privacy-first:

- Default PII (such as IP address) is not sent.
- Query strings are stripped.
- Sensitive headers (Authorization/Cookie/Set-Cookie) are filtered.

If you want the SDK to include default PII, opt in:

```python
tracker = ErrorTracker(
    dsn="https://xrayradar.com/your_project_id",
    send_default_pii=True
)
```

## Framework Integrations

### Flask

```python
from flask import Flask
from xrayradar import ErrorTracker
from xrayradar.integrations import FlaskIntegration

app = Flask(__name__)

# Initialize error tracker with your XrayRadar DSN
tracker = ErrorTracker(dsn="https://xrayradar.com/your_project_id")

# Setup Flask integration
flask_integration = FlaskIntegration(app, tracker)

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/error')
def error():
    # This will be automatically captured
    raise ValueError("Something went wrong!")
```

### Django

Add the middleware to your Django settings:

```python
# settings.py
MIDDLEWARE = [
    'xrayradar.integrations.django.ErrorTrackerMiddleware',
    # ... other middleware
]

# Optional: Configure via Django settings
# Replace with your actual XrayRadar DSN from your project settings
XRAYRADAR_DSN = "https://xrayradar.com/your_project_id"
XRAYRADAR_ENVIRONMENT = "production"
XRAYRADAR_RELEASE = "1.0.0"
```

### Graphene (GraphQL)

GraphQL frameworks often catch resolver exceptions and return them as part of the GraphQL response, so Django's normal exception hooks may not see them.

Use the Graphene middleware to capture resolver exceptions (Queries and Mutations):

```python
from xrayradar.integrations.graphene import GrapheneIntegration

graphql_middleware = [GrapheneIntegration()]

# Example usage with GraphQLView / FileUploadGraphQLView:
# FileUploadGraphQLView.as_view(schema=schema, middleware=graphql_middleware)
```

### Django REST Framework (DRF)

DRF exceptions are typically handled and converted into responses by the DRF exception handler. Use the handler wrapper to report server-side errors.

```python
from xrayradar.integrations.drf import make_drf_exception_handler

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": make_drf_exception_handler(),
}
```

### FastAPI

```python
from fastapi import FastAPI
from xrayradar import ErrorTracker
from xrayradar.integrations import FastAPIIntegration

app = FastAPI()

# Initialize error tracker with your XrayRadar DSN
tracker = ErrorTracker(dsn="https://xrayradar.com/your_project_id")

# Setup FastAPI integration
fastapi_integration = FastAPIIntegration(app, tracker)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/error")
async def error():
    # This will be automatically captured
    raise ValueError("Something went wrong!")
```

## Advanced Usage

### Custom Context

```python
from xrayradar import ErrorTracker

tracker = ErrorTracker(dsn="https://xrayradar.com/your_project_id")

# Set user context
tracker.set_user(
    id="123",
    email="user@example.com",
    username="johndoe"
)

# Add tags
tracker.set_tag("feature", "checkout")
tracker.set_tag("locale", "en-US")

# Add extra context
tracker.set_extra("cart_value", 99.99)
tracker.set_extra("payment_method", "credit_card")

# Add breadcrumbs
tracker.add_breadcrumb(
    message="User clicked checkout button",
    category="user",
    level="info"
)

# Capture exception with additional context
try:
    process_payment()
except Exception as e:
    tracker.capture_exception(e, payment_stage="processing")
```

### Before Send Callback

```python
from xrayradar import ErrorTracker, Event

def before_send(event: Event) -> Event:
    # Filter out certain errors
    if "404" in event.message:
        return None  # Don't send 404 errors
    
    # Modify event data
    event.contexts.tags["processed_by"] = "before_send"
    
    return event

tracker = ErrorTracker(
    dsn="https://xrayradar.com/your_project_id",
    before_send=before_send
)
```

### Configuration File

Create a configuration file (`xrayradar.json`):

```json
{
    "dsn": "https://xrayradar.com/your_project_id",
    "environment": "production",
    "release": "1.0.0",
    "sample_rate": 0.5,
    "max_breadcrumbs": 50,
    "timeout": 5.0,
    "verify_ssl": true,
    "auth_token": "your_token_here"
}
```

Load it in your code:

```python
from xrayradar.config import load_config
from xrayradar import ErrorTracker

config = load_config("xrayradar.json")
tracker = ErrorTracker(**config.to_dict())
```

## API Reference

### ErrorTracker

Main client class for error tracking.

#### Parameters

- `dsn` (str, optional): Data Source Name for connecting to the server
- `debug` (bool, default=False): Enable debug mode (prints to console)
- `environment` (str, default="development"): Environment name
- `release` (str, optional): Release version
- `server_name` (str, optional): Server name
- `sample_rate` (float, default=1.0): Sampling rate (0.0 to 1.0)
- `max_breadcrumbs` (int, default=100): Maximum number of breadcrumbs
- `before_send` (callable, optional): Callback to modify events before sending
- `transport` (Transport, optional): Custom transport implementation

#### Methods

- `capture_exception(exception=None, level=Level.ERROR, message=None, **extra_context)`: Capture an exception
- `capture_message(message, level=Level.ERROR, **extra_context)`: Capture a message
- `add_breadcrumb(message, category=None, level=None, data=None, timestamp=None)`: Add a breadcrumb
- `set_user(**user_data)`: Set user context
- `set_tag(key, value)`: Set a tag
- `set_extra(key, value)`: Set extra context data
- `set_context(context_type, context_data)`: Set context data
- `clear_breadcrumbs()`: Clear all breadcrumbs
- `flush(timeout=None)`: Flush any pending events
- `close()`: Close the client and cleanup resources

### Global Functions

- `init(**kwargs)`: Initialize the global error tracker client
- `get_client()`: Get the global error tracker client
- `capture_exception(*args, **kwargs)`: Capture an exception using the global client
- `capture_message(message, *args, **kwargs)`: Capture a message using the global client
- `add_breadcrumb(*args, **kwargs)`: Add a breadcrumb using the global client
- `set_user(**user_data)`: Set user context using the global client
- `set_tag(key, value)`: Set a tag using the global client
- `set_extra(key, value)`: Set extra context data using the global client

## Data Models

### Event

Represents an error tracking event with the following fields:

- `event_id`: Unique identifier for the event
- `timestamp`: Event timestamp
- `level`: Error level (fatal, error, warning, info, debug)
- `message`: Event message
- `platform`: Platform (always "python")
- `sdk`: SDK information
- `contexts`: Event context (user, request, tags, extra)
- `exception`: Exception information (if applicable)
- `breadcrumbs`: List of breadcrumbs
- `fingerprint`: Event fingerprint for grouping
- `modules`: Loaded Python modules

### Context

Contains context information:

- `user`: User information
- `request`: HTTP request information
- `tags`: Key-value tags
- `extra`: Additional context data
- `server_name`: Server name
- `release`: Release version
- `environment`: Environment name

## Transport Layer

The SDK supports multiple transport implementations:

- `HttpTransport`: Sends events via HTTP to a server
- `DebugTransport`: Prints events to console (for development)
- `NullTransport`: Discards all events (for testing)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/KingPegasus/XrayRadar.git
cd xrayradar

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run linting
flake8 src/
black src/

# Type checking
mypy src/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xrayradar

# Run specific test file
pytest tests/test_client.py
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Support

For bug reports and feature requests, please use the GitHub issue tracker.
