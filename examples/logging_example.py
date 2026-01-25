#!/usr/bin/env python3
"""
Python logging integration example for xrayradar
"""

import logging
from xrayradar import ErrorTracker
from xrayradar.integrations.logging import setup_logging, LoggingIntegration

# Initialize error tracker with your XrayRadar DSN
# Replace with your actual DSN from your XrayRadar project settings
# Format: https://xrayradar.com/your_project_id
tracker = ErrorTracker(
    dsn="https://xrayradar.com/your_project_id",
    environment="development",
    release="1.0.0",
    debug=True,  # Enable debug mode to see events in console
    # auth_token="your_token_here",  # Required for XrayRadar authentication
)

# Setup logging integration
# This will capture WARNING, ERROR, and CRITICAL log messages by default
integration = setup_logging(
    client=tracker,
    level=logging.WARNING,  # Only capture WARNING and above
    exclude_loggers={"urllib3", "requests"}  # Exclude noisy third-party loggers
)

print("Python Logging Integration Example")
print("=" * 40)

# Configure Python logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get a logger
logger = logging.getLogger("myapp")

print("\n1. Logging different levels:")
print("   (Only WARNING and above will be sent to XrayRadar)")

# These will NOT be sent (below WARNING level)
logger.debug("Debug message - not sent to XrayRadar")
logger.info("Info message - not sent to XrayRadar")

# These WILL be sent to XrayRadar
logger.warning("Warning message - sent to XrayRadar")
logger.error("Error message - sent to XrayRadar")
logger.critical("Critical message - sent to XrayRadar")

print("\n2. Logging exceptions:")
try:
    result = 1 / 0
except ZeroDivisionError:
    # Log exception with exception info
    logger.exception("Division by zero occurred")
    # This will be captured as an exception in XrayRadar

print("\n3. Excluding specific loggers:")
# Create a logger that's excluded
urllib3_logger = logging.getLogger("urllib3")
urllib3_logger.warning("This won't be sent (logger is excluded)")

print("\n4. Custom logger with context:")
# Add context before logging
tracker.set_tag("module", "payment")
tracker.set_extra("transaction_id", "txn_12345")
logger.error("Payment processing failed")

print("\n5. Teardown integration:")
# Remove the logging integration
integration.teardown()
logger.error("This won't be sent (integration removed)")

print("\n" + "=" * 40)
print("Example completed! Check the console output above for captured events.")
print("In production, these log messages would be sent to your XrayRadar dashboard.")
