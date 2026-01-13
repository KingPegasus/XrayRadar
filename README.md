# XrayRadar

A Python error tracking SDK for capturing, processing, and sending error events to a tracking server.

## Features

- **Automatic Exception Capture**: Automatically captures uncaught exceptions
- **Manual Error Reporting**: Capture exceptions and messages manually
- **Rich Context**: Collects breadcrumbs, tags, and custom context
- **Framework Integrations**: Built-in integrations for Flask, Django, and FastAPI
- **Flexible Transport**: HTTP transport with retry logic and rate limiting
- **Sampling**: Configurable sampling to reduce noise
- **Debug Mode**: Console output for development and testing
- **Configuration**: Environment variables and file-based configuration

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

# Initialize the SDK
tracker = ErrorTracker(
    dsn="https://your_public_key@your_host.com/your_project_id",
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

# Or use the global client
xrayradar.init(
    dsn="https://your_public_key@your_host.com/your_project_id",
    environment="production",
)

try:
    1 / 0
except Exception:
    xrayradar.capture_exception()
```

### Environment Variables

You can configure the SDK using environment variables:

```bash
export XRAYRADAR_DSN="https://your_public_key@your_host.com/your_project_id"
export XRAYRADAR_ENVIRONMENT="production"
export XRAYRADAR_RELEASE="1.0.0"
export XRAYRADAR_SAMPLE_RATE="0.5"
export XRAYRADAR_SEND_DEFAULT_PII="false"
```

## Privacy

By default, `xrayradar` is privacy-first:

- Default PII (such as IP address) is not sent.
- Query strings are stripped.
- Sensitive headers (Authorization/Cookie/Set-Cookie) are filtered.

If you want the SDK to include default PII, opt in:

```python
tracker = ErrorTracker(dsn="your_dsn_here", send_default_pii=True)
```

## Framework Integrations

### Flask

```python
from flask import Flask
from xrayradar import ErrorTracker
from xrayradar.integrations import FlaskIntegration

app = Flask(__name__)

# Initialize error tracker
tracker = ErrorTracker(dsn="your_dsn_here")

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

# Optional: Configure via settings
XRAYRADAR_DSN = "https://your_public_key@your_host.com/your_project_id"
XRAYRADAR_ENVIRONMENT = "production"
XRAYRADAR_RELEASE = "1.0.0"
```

### FastAPI

```python
from fastapi import FastAPI
from xrayradar import ErrorTracker
from xrayradar.integrations import FastAPIIntegration

app = FastAPI()

# Initialize error tracker
tracker = ErrorTracker(dsn="your_dsn_here")

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

tracker = ErrorTracker(dsn="your_dsn_here")

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
    dsn="your_dsn_here",
    before_send=before_send
)
```

### Configuration File

Create a configuration file (`xrayradar.json`):

```json
{
    "dsn": "https://your_public_key@your_host.com/your_project_id",
    "environment": "production",
    "release": "1.0.0",
    "sample_rate": 0.5,
    "max_breadcrumbs": 50,
    "timeout": 5.0,
    "verify_ssl": true
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
git clone https://github.com/<your-org-or-username>/xrayradar.git
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
