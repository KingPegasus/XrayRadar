#!/usr/bin/env python3
"""
Basic usage example for xrayradar
"""

import xrayradar
from xrayradar import ErrorTracker, Level


def main():
    # Initialize the SDK with your XrayRadar DSN
    # Replace with your actual DSN from your XrayRadar project settings
    # Format: https://xrayradar.com/your_project_id
    tracker = ErrorTracker(
        dsn="https://xrayradar.com/your_project_id",
        environment="development",
        release="1.0.0",
        debug=True,  # Enable debug mode to see events in console
        # auth_token="your_token_here",  # Required for XrayRadar authentication
    )

    print("xrayradar Basic Usage Example")
    print("=" * 40)

    # Example 1: Capture an exception
    print("\n1. Capturing an exception:")
    try:
        result = 1 / 0
    except Exception as e:
        event_id = tracker.capture_exception(e)
        print(f"   Exception captured with event ID: {event_id}")

    # Example 2: Capture a message
    print("\n2. Capturing a message:")
    event_id = tracker.capture_message(
        "User login failed",
        level=Level.WARNING,
        user_id="123",
        username="johndoe"
    )
    print(f"   Message captured with event ID: {event_id}")

    # Example 3: Set user context
    print("\n3. Setting user context:")
    tracker.set_user(
        id="123",
        email="user@example.com",
        username="johndoe"
    )
    print("   User context set")

    # Example 4: Add tags and extra context
    print("\n4. Adding tags and extra context:")
    tracker.set_tag("feature", "checkout")
    tracker.set_tag("locale", "en-US")
    tracker.set_extra("cart_value", 99.99)
    tracker.set_extra("payment_method", "credit_card")
    print("   Tags and extra context added")

    # Example 5: Add breadcrumbs
    print("\n5. Adding breadcrumbs:")
    tracker.add_breadcrumb(
        message="User clicked checkout button",
        category="user",
        level=Level.INFO
    )
    tracker.add_breadcrumb(
        message="Payment processing started",
        category="payment",
        level=Level.INFO
    )
    print("   Breadcrumbs added")

    # Example 6: Capture exception with context
    print("\n6. Capturing exception with context:")
    try:
        # Simulate a payment processing error
        raise ValueError("Payment gateway timeout")
    except Exception as e:
        event_id = tracker.capture_exception(
            e,
            payment_stage="processing",
            payment_amount=99.99,
            gateway="stripe"
        )
        print(f"   Exception with context captured with event ID: {event_id}")

    # Example 7: Using global client
    print("\n7. Using global client:")
    xrayradar.init(
        dsn="https://xrayradar.com/your_project_id",
        environment="development",
        debug=True,
        # auth_token="your_token_here",  # Required for XrayRadar authentication
    )

    try:
        # This will use the global client
        raise RuntimeError("Global client test error")
    except Exception:
        event_id = xrayradar.capture_exception()
        print(
            f"   Exception captured via global client with event ID: {event_id}")

    # Example 8: Different log levels
    print("\n8. Different log levels:")
    xrayradar.capture_message("Debug message", level=Level.DEBUG)
    xrayradar.capture_message("Info message", level=Level.INFO)
    xrayradar.capture_message("Warning message", level=Level.WARNING)
    xrayradar.capture_message("Error message", level=Level.ERROR)
    xrayradar.capture_message("Fatal message", level=Level.FATAL)
    print("   Messages with different levels captured")

    # Cleanup
    print("\n9. Cleaning up:")
    tracker.close()
    print("   Client closed")

    print("\n" + "=" * 40)
    print("Example completed! Check the console output above for captured events.")
    print("In production, these events would be sent to your error tracking service.")


if __name__ == "__main__":
    main()
