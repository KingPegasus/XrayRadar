#!/usr/bin/env python3
"""
FastAPI integration example for xrayradar
"""

from typing import Optional

from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Request
import uvicorn
from xrayradar import ErrorTracker
from xrayradar.integrations import FastAPIIntegration

# Create FastAPI app
app = FastAPI(title="XrayRadar FastAPI Example")

# Initialize error tracker
tracker = ErrorTracker(
    dsn="https://your_public_key@your_host.com/your_project_id",
    environment="development",
    release="1.0.0",
    debug=True,  # Enable debug mode to see events in console
)

# Setup FastAPI integration
fastapi_integration = FastAPIIntegration(app, tracker)

# Pydantic models


class CalculationInput(BaseModel):
    operation: str
    a: float
    b: float


class UserCreate(BaseModel):
    username: str
    email: str
    age: Optional[int] = None


# In-memory "database"
users_db = {}
user_id_counter = 1


@app.get("/")
async def root():
    """Root endpoint"""
    tracker.add_breadcrumb(
        message="User visited root endpoint",
        category="navigation",
        level="info"
    )
    return {
        "message": "Welcome to the FastAPI Error Tracker Example!",
        "endpoints": [
            "/",
            "/hello/{name}",
            "/users/",
            "/users/{user_id}",
            "/calculate",
            "/error",
            "/manual-error"
        ]
    }


@app.get("/hello/{name}")
async def hello(name: str):
    """Personalized greeting"""
    tracker.set_user(username=name)
    tracker.add_breadcrumb(
        message=f"Greeting requested for {name}",
        category="user",
        level="info"
    )
    return {"message": f"Hello, {name}!"}


@app.get("/error")
async def trigger_error():
    """Trigger an error to test error tracking"""
    tracker.add_breadcrumb(
        message="User accessed error endpoint",
        category="user",
        level="warning"
    )

    # This will be automatically captured by the FastAPI integration
    raise ValueError("This is a test error from FastAPI!")


@app.post("/users/")
async def create_user(user: UserCreate):
    """Create a new user"""
    global user_id_counter

    try:
        # Validate user data
        if user.age and user.age < 0:
            raise ValueError("Age cannot be negative")

        # Create user
        user_id = user_id_counter
        user_id_counter += 1

        user_data = {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "age": user.age
        }

        users_db[user_id] = user_data

        # Set user context
        tracker.set_user(
            id=str(user_id),
            username=user.username,
            email=user.email
        )

        tracker.add_breadcrumb(
            message=f"User created: {user.username}",
            category="user",
            level="info",
            data={"user_id": user_id}
        )

        return user_data

    except ValueError as e:
        # Manual error capture with context
        tracker.capture_exception(
            e,
            endpoint="/users/",
            method="POST",
            username=user.username,
            validation_error=True
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID"""
    if user_id not in users_db:
        tracker.capture_message(
            f"User not found: {user_id}",
            level="warning",
            user_id=user_id,
            endpoint="/users/{user_id}"
        )
        raise HTTPException(status_code=404, detail="User not found")

    user_data = users_db[user_id]

    # Set user context
    tracker.set_user(
        id=str(user_id),
        username=user_data["username"],
        email=user_data["email"]
    )

    tracker.add_breadcrumb(
        message=f"User profile viewed: {user_data['username']}",
        category="user",
        level="info"
    )

    return user_data


@app.post("/calculate")
async def calculate(calc_input: CalculationInput):
    """Perform calculations"""
    try:
        operation = calc_input.operation
        a = calc_input.a
        b = calc_input.b

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

        return {
            "operation": operation,
            "operands": [a, b],
            "result": result
        }

    except ValueError as e:
        # Manual error capture with additional context
        tracker.capture_exception(
            e,
            endpoint="/calculate",
            method="POST",
            operation=operation,
            operands=[a, b],
            api_version="v1"
        )

        raise HTTPException(status_code=400, detail=str(e))


@app.get("/manual-error")
async def manual_error():
    """Manually capture an error"""
    try:
        # Simulate some operation that might fail
        import random
        if random.random() < 0.5:
            raise RuntimeError("Random operation failed!")

        return {"message": "Operation succeeded!"}

    except Exception as e:
        # Manually capture the exception with context
        event_id = tracker.capture_exception(
            e,
            endpoint="/manual-error",
            random_seed=True
        )

        return {
            "error": str(e),
            "event_id": event_id,
            "message": "Error captured and logged"
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    # This is handled by the FastAPI integration, but we can add additional context
    tracker.set_extra("handled_by", "global_exception_handler")
    tracker.set_tag("exception_type", type(exc).__name__)

    # Re-raise to let the integration handle it
    raise exc

if __name__ == "__main__":
    print("FastAPI xrayradar Example")
    print("=" * 40)
    print("Available endpoints:")
    print("  GET  /                    - Root")
    print("  GET  /hello/{name}        - Personalized greeting")
    print("  POST /users/              - Create user")
    print("  GET  /users/{user_id}     - Get user")
    print("  POST /calculate           - Calculator API")
    print("  GET  /error               - Triggers an error")
    print("  GET  /manual-error        - Manual error capture")
    print("\nTry these URLs:")
    print("  http://localhost:8000/")
    print("  http://localhost:8000/hello/world")
    print("  http://localhost:8000/error")
    print("  http://localhost:8000/nonexistent")
    print("\nFor creating users:")
    print('  curl -X POST http://localhost:8000/users/ \\')
    print('       -H "Content-Type: application/json" \\')
    print(
        '       -d \'{"username": "john", "email": "john@example.com", "age": 30}\'')
    print("\nFor the calculator API:")
    print('  curl -X POST http://localhost:8000/calculate \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"operation": "add", "a": 5, "b": 3}\'')
    print("\nStarting FastAPI app...")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
