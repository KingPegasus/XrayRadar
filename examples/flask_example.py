#!/usr/bin/env python3
"""
Flask integration example for xrayradar
"""

from flask import Flask, jsonify, request
from xrayradar import ErrorTracker
from xrayradar.integrations import FlaskIntegration

# Create Flask app
app = Flask(__name__)

# Initialize error tracker
tracker = ErrorTracker(
    dsn="https://your_public_key@your_host.com/your_project_id",
    environment="development",
    release="1.0.0",
    debug=True,  # Enable debug mode to see events in console
)

# Setup Flask integration
flask_integration = FlaskIntegration(app, tracker)


@app.route('/')
def index():
    """Home page"""
    tracker.add_breadcrumb(
        message="User visited home page",
        category="navigation",
        level="info"
    )
    return jsonify({
        "message": "Welcome to the Flask Error Tracker Example!",
        "endpoints": [
            "/",
            "/hello/<name>",
            "/error",
            "/user/<user_id>",
            "/api/calculate"
        ]
    })


@app.route('/hello/<name>')
def hello(name):
    """Personalized greeting"""
    tracker.set_user(username=name)
    tracker.add_breadcrumb(
        message=f"Greeting requested for {name}",
        category="user",
        level="info"
    )
    return jsonify({"message": f"Hello, {name}!"})


@app.route('/error')
def trigger_error():
    """Trigger an error to test error tracking"""
    tracker.add_breadcrumb(
        message="User accessed error endpoint",
        category="user",
        level="warning"
    )

    # This will be automatically captured by the Flask integration
    raise ValueError("This is a test error from Flask!")


@app.route('/user/<user_id>')
def user_profile(user_id):
    """User profile page"""
    # Set user context
    tracker.set_user(
        id=user_id,
        email=f"user{user_id}@example.com",
        username=f"user_{user_id}"
    )

    tracker.add_breadcrumb(
        message=f"User {user_id} profile viewed",
        category="user",
        level="info"
    )

    # Simulate some user data
    user_data = {
        "id": user_id,
        "email": f"user{user_id}@example.com",
        "username": f"user_{user_id}",
        "last_login": "2024-01-10T10:30:00Z"
    }

    return jsonify(user_data)


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """API endpoint that performs calculations"""
    try:
        data = request.get_json()

        if not data:
            raise ValueError("No JSON data provided")

        operation = data.get('operation')
        a = data.get('a')
        b = data.get('b')

        if operation == 'add':
            result = a + b
        elif operation == 'subtract':
            result = a - b
        elif operation == 'multiply':
            result = a * b
        elif operation == 'divide':
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

        tracker.add_breadcrumb(
            message=f"Calculation performed: {operation}({a}, {b}) = {result}",
            category="api",
            level="info"
        )

        return jsonify({
            "operation": operation,
            "operands": [a, b],
            "result": result
        })

    except Exception as e:
        # Manual error capture with additional context
        tracker.capture_exception(
            e,
            endpoint="/api/calculate",
            method=request.method,
            operation=data.get('operation') if data else None,
            api_version="v1"
        )

        return jsonify({
            "error": str(e),
            "message": "Calculation failed"
        }), 400


@app.route('/manual-error')
def manual_error():
    """Manually capture an error"""
    try:
        # Simulate some operation that might fail
        import random
        if random.random() < 0.5:
            raise RuntimeError("Random operation failed!")

        return jsonify({"message": "Operation succeeded!"})

    except Exception as e:
        # Manually capture the exception with context
        event_id = tracker.capture_exception(
            e,
            endpoint="/manual-error",
            user_agent=request.headers.get('User-Agent'),
            random_seed=True
        )

        return jsonify({
            "error": str(e),
            "event_id": event_id,
            "message": "Error captured and logged"
        })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    tracker.capture_message(
        f"404 Not Found: {request.path}",
        level="warning",
        path=request.path,
        method=request.method,
        referer=request.headers.get('Referer')
    )
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    tracker.capture_exception(
        error,
        path=request.path,
        method=request.method
    )
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    print("Flask xrayradar Example")
    print("=" * 40)
    print("Available endpoints:")
    print("  GET  /           - Home page")
    print("  GET  /hello/<name> - Personalized greeting")
    print("  GET  /error      - Triggers an error")
    print("  GET  /user/<id>  - User profile")
    print("  POST /api/calculate - Calculator API")
    print("  GET  /manual-error - Manual error capture")
    print("\nTry these URLs:")
    print("  http://localhost:5000/")
    print("  http://localhost:5000/hello/world")
    print("  http://localhost:5000/error")
    print("  http://localhost:5000/user/123")
    print("  http://localhost:5000/nonexistent")
    print("\nFor the calculator API:")
    print('  curl -X POST http://localhost:5000/api/calculate \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"operation": "add", "a": 5, "b": 3}\'')
    print("\nStarting Flask app...")

    app.run(debug=True, port=5000)
