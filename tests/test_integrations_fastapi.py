import asyncio
import importlib
import sys
from types import SimpleNamespace

import pytest

from xrayradar.client import ErrorTracker
from xrayradar.integrations.fastapi import FastAPIIntegration


def test_fastapi_integration_captures_exception(monkeypatch):
    captured = {}

    class FakeClient:
        def capture_exception(self, exc, request=None, tags=None, **kwargs):
            captured["exc"] = exc
            captured["request"] = request
            captured["tags"] = tags
            return "event-id"

    class DummyURL:
        def __init__(self):
            self.path = "/error"
            self.query = "a=1"
            self.hostname = "testserver"
            self.port = 8000

        def __str__(self):
            return "http://testserver/error?a=1"

    class DummyClient:
        host = "127.0.0.1"

    class DummyFastAPIRequest:
        method = "GET"
        url = DummyURL()
        client = DummyClient()
        headers = {"User-Agent": "pytest", "Authorization": "Bearer secret"}

    integration = FastAPIIntegration(fastapi_app=None)
    integration.client = FakeClient()  # type: ignore[assignment]

    async def run():
        with pytest.raises(RuntimeError):
            await integration._handle_exception(DummyFastAPIRequest(), RuntimeError("boom"))

    asyncio.run(run())

    assert isinstance(captured.get("exc"), RuntimeError)
    assert captured["tags"]["framework"] == "fastapi"
    assert captured["request"]["url"] == "http://testserver/error?a=1"
    assert "Authorization" not in captured["request"]["headers"]


def test_fastapi_integration_init_app_and_middleware_dispatch(monkeypatch):
    # Stub the fastapi/starlette imports so the integration module enables middleware.
    fastapi_mod = SimpleNamespace()

    class RequestValidationError(Exception):
        pass

    class FastAPI:
        def __init__(self):
            self.handlers = []
            self.middlewares = []

        def add_exception_handler(self, exc_type, handler):
            self.handlers.append((exc_type, handler))

        def add_middleware(self, middleware_cls, **kwargs):
            self.middlewares.append((middleware_cls, kwargs))

    class Request:
        method = "GET"

        class _URL:
            path = "/x"
            query = ""
            hostname = "h"
            port = 80

            def __str__(self):
                return "http://h/x"

        url = _URL()
        client = None
        headers = {"cookie": "x", "X": "1"}

    fastapi_mod.FastAPI = FastAPI
    fastapi_mod.Request = Request

    fastapi_ex_mod = SimpleNamespace(
        RequestValidationError=RequestValidationError)

    starlette_mw_mod = SimpleNamespace()

    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app

    starlette_mw_mod.BaseHTTPMiddleware = BaseHTTPMiddleware

    starlette_exc_mod = SimpleNamespace(HTTPException=type(
        "StarletteHTTPException", (Exception,), {}))

    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.exceptions", fastapi_ex_mod)
    monkeypatch.setitem(
        sys.modules, "starlette.middleware.base", starlette_mw_mod)
    monkeypatch.setitem(sys.modules, "starlette.exceptions", starlette_exc_mod)

    import xrayradar.integrations.fastapi as fastapi_integration

    importlib.reload(fastapi_integration)

    app = fastapi_integration.FastAPI()

    captured = {"n": 0}

    class FakeClient:
        def __init__(self):
            self.breadcrumbs = 0
            self.contexts = []

        def clear_breadcrumbs(self):
            self.breadcrumbs += 1

        def add_breadcrumb(self, **kwargs):
            self.contexts.append(("breadcrumb", kwargs))

        def set_context(self, context_type, context_data):
            self.contexts.append((context_type, context_data))

        def capture_exception(self, *a, **k):
            captured["n"] += 1

        def capture_message(self, *a, **k):
            captured["n"] += 1

    client = FakeClient()
    integration = fastapi_integration.FastAPIIntegration()
    integration.init_app(app, client=client)

    assert len(app.handlers) == 3
    assert len(app.middlewares) == 1

    middleware_cls, kwargs = app.middlewares[0]
    middleware = middleware_cls(app, **kwargs)

    class DummyReq:
        method = "GET"

        class _URL:
            path = "/x"
            query = "a=1"
            hostname = "h"
            port = 80

            def __str__(self):
                return "http://h/x?a=1"

        url = _URL()
        client = None
        headers = {"authorization": "secret", "x": "1"}

    async def call_next(_req):
        return "ok"

    async def run_dispatch():
        await middleware.dispatch(DummyReq(), call_next)

    asyncio.run(run_dispatch())

    # Exercise validation and http exception handlers.
    async def run_handlers():
        with pytest.raises(RequestValidationError):
            await integration._handle_validation_error(DummyReq(), RequestValidationError("bad"))

        StarletteHTTPException = fastapi_integration.StarletteHTTPException
        exc = StarletteHTTPException("boom")
        exc.status_code = 400
        exc.detail = "bad"
        with pytest.raises(StarletteHTTPException):
            await integration._handle_http_exception(DummyReq(), exc)

    asyncio.run(run_handlers())
    assert captured["n"] >= 2


def test_fastapi_integration_init_app_importerror_when_fastapi_missing(monkeypatch):
    import xrayradar.integrations.fastapi as fastapi_mod

    integration = fastapi_mod.FastAPIIntegration()
    monkeypatch.setattr(fastapi_mod, "FastAPI", None)

    with pytest.raises(ImportError):
        integration.init_app(object(), client=ErrorTracker(
            debug=True))  # type: ignore[arg-type]


def test_fastapi_integration_constructor_auto_inits_when_app_passed(monkeypatch):
    # Stub modules so the integration sees FastAPI at import time.
    fastapi_mod = SimpleNamespace()

    class FastAPI:
        def __init__(self):
            self.handlers = []
            self.middlewares = []

        def add_exception_handler(self, exc_type, handler):
            self.handlers.append((exc_type, handler))

        def add_middleware(self, middleware_cls, **kwargs):
            self.middlewares.append((middleware_cls, kwargs))

    fastapi_mod.FastAPI = FastAPI
    fastapi_mod.Request = object
    fastapi_ex_mod = SimpleNamespace(RequestValidationError=type(
        "RequestValidationError", (Exception,), {}))
    starlette_mw_mod = SimpleNamespace(BaseHTTPMiddleware=type(
        "BaseHTTPMiddleware", (), {"__init__": lambda self, app: None}))
    starlette_exc_mod = SimpleNamespace(HTTPException=type(
        "StarletteHTTPException", (Exception,), {}))

    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.exceptions", fastapi_ex_mod)
    monkeypatch.setitem(
        sys.modules, "starlette.middleware.base", starlette_mw_mod)
    monkeypatch.setitem(sys.modules, "starlette.exceptions", starlette_exc_mod)

    import xrayradar.integrations.fastapi as fastapi_integration
    importlib.reload(fastapi_integration)

    app = fastapi_integration.FastAPI()
    integration = fastapi_integration.FastAPIIntegration(app)
    assert len(app.handlers) == 3
    assert len(app.middlewares) == 1


def test_fastapi_handlers_raise_when_no_client(monkeypatch):
    import xrayradar.integrations.fastapi as fastapi_mod

    integration = fastapi_mod.FastAPIIntegration()
    integration.client = None

    class DummyReq:
        method = "GET"
        url = SimpleNamespace(query="", __str__=lambda self: "http://x")
        headers = {}
        client = None

    async def run():
        with pytest.raises(RuntimeError):
            await integration._handle_exception(DummyReq(), RuntimeError("x"))

    asyncio.run(run())


def test_fastapi_middleware_dispatch_skips_when_client_none(monkeypatch):
    # Reload with stubs so ErrorTrackerMiddleware exists.
    fastapi_mod = SimpleNamespace()

    class FastAPI:
        def __init__(self):
            self.handlers = []
            self.middlewares = []

        def add_exception_handler(self, exc_type, handler):
            self.handlers.append((exc_type, handler))

        def add_middleware(self, middleware_cls, **kwargs):
            self.middlewares.append((middleware_cls, kwargs))

    class Request:
        method = "GET"
        url = SimpleNamespace(path="/", query="", hostname="h",
                              port=80, __str__=lambda self: "http://h/")
        headers = {}
        client = None

    fastapi_mod.FastAPI = FastAPI
    fastapi_mod.Request = Request
    fastapi_ex_mod = SimpleNamespace(RequestValidationError=type(
        "RequestValidationError", (Exception,), {}))
    starlette_mw_mod = SimpleNamespace(BaseHTTPMiddleware=type(
        "BaseHTTPMiddleware", (), {"__init__": lambda self, app: None}))
    starlette_exc_mod = SimpleNamespace(HTTPException=type(
        "StarletteHTTPException", (Exception,), {}))

    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.exceptions", fastapi_ex_mod)
    monkeypatch.setitem(
        sys.modules, "starlette.middleware.base", starlette_mw_mod)
    monkeypatch.setitem(sys.modules, "starlette.exceptions", starlette_exc_mod)

    import xrayradar.integrations.fastapi as fastapi_integration
    importlib.reload(fastapi_integration)

    middleware = fastapi_integration.ErrorTrackerMiddleware(
        app=None, client=None)
    middleware.client = None

    async def call_next(_req):
        return "ok"

    async def run():
        out = await middleware.dispatch(Request(), call_next)
        assert out == "ok"

    asyncio.run(run())


def test_fastapi_middleware_is_none_when_base_http_middleware_missing(monkeypatch):
    # Force the import block to fail by providing a starlette.middleware.base module
    # that does NOT provide BaseHTTPMiddleware.
    fastapi_mod = SimpleNamespace(FastAPI=object, Request=object)
    fastapi_ex_mod = SimpleNamespace(RequestValidationError=type(
        "RequestValidationError", (Exception,), {}))
    starlette_mw_mod = SimpleNamespace()
    starlette_exc_mod = SimpleNamespace(HTTPException=type(
        "StarletteHTTPException", (Exception,), {}))

    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.exceptions", fastapi_ex_mod)
    monkeypatch.setitem(
        sys.modules, "starlette.middleware.base", starlette_mw_mod)
    monkeypatch.setitem(sys.modules, "starlette.exceptions", starlette_exc_mod)

    import xrayradar.integrations.fastapi as fastapi_integration
    importlib.reload(fastapi_integration)
    assert fastapi_integration.ErrorTrackerMiddleware is None


def test_init_fastapi_integration_returns_instance(monkeypatch):
    # Reload with stubs so init_fastapi_integration can construct successfully.
    fastapi_mod = SimpleNamespace()

    class FastAPI:
        def __init__(self):
            self.handlers = []
            self.middlewares = []

        def add_exception_handler(self, exc_type, handler):
            self.handlers.append((exc_type, handler))

        def add_middleware(self, middleware_cls, **kwargs):
            self.middlewares.append((middleware_cls, kwargs))

    fastapi_mod.FastAPI = FastAPI
    fastapi_mod.Request = object
    fastapi_ex_mod = SimpleNamespace(RequestValidationError=type(
        "RequestValidationError", (Exception,), {}))
    starlette_mw_mod = SimpleNamespace(BaseHTTPMiddleware=type(
        "BaseHTTPMiddleware", (), {"__init__": lambda self, app: None}))
    starlette_exc_mod = SimpleNamespace(HTTPException=type(
        "StarletteHTTPException", (Exception,), {}))

    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.exceptions", fastapi_ex_mod)
    monkeypatch.setitem(
        sys.modules, "starlette.middleware.base", starlette_mw_mod)
    monkeypatch.setitem(sys.modules, "starlette.exceptions", starlette_exc_mod)

    import xrayradar.integrations.fastapi as fastapi_integration
    importlib.reload(fastapi_integration)

    app = fastapi_integration.FastAPI()
    client = ErrorTracker(debug=True)
    integration = fastapi_integration.init_fastapi_integration(
        app, client=client)
    assert isinstance(integration, fastapi_integration.FastAPIIntegration)
    assert integration.client is client


def test_fastapi_handlers_raise_validation_and_http_when_no_client(monkeypatch):
    # Reload with stubs so RequestValidationError / StarletteHTTPException are concrete.
    fastapi_mod = SimpleNamespace()

    class FastAPI:
        def __init__(self):
            self.handlers = []
            self.middlewares = []

        def add_exception_handler(self, exc_type, handler):
            self.handlers.append((exc_type, handler))

        def add_middleware(self, middleware_cls, **kwargs):
            self.middlewares.append((middleware_cls, kwargs))

    class Request:
        method = "GET"
        url = SimpleNamespace(path="/", query="", hostname="h",
                              port=80, __str__=lambda self: "http://h/")
        headers = {}
        client = None

    class RequestValidationError(Exception):
        pass

    class StarletteHTTPException(Exception):
        def __init__(self, msg):
            super().__init__(msg)
            self.status_code = 400
            self.detail = "bad"

    fastapi_mod.FastAPI = FastAPI
    fastapi_mod.Request = Request
    fastapi_ex_mod = SimpleNamespace(
        RequestValidationError=RequestValidationError)
    starlette_mw_mod = SimpleNamespace(BaseHTTPMiddleware=type(
        "BaseHTTPMiddleware", (), {"__init__": lambda self, app: None}))
    starlette_exc_mod = SimpleNamespace(HTTPException=StarletteHTTPException)

    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.exceptions", fastapi_ex_mod)
    monkeypatch.setitem(
        sys.modules, "starlette.middleware.base", starlette_mw_mod)
    monkeypatch.setitem(sys.modules, "starlette.exceptions", starlette_exc_mod)

    import xrayradar.integrations.fastapi as fastapi_integration
    importlib.reload(fastapi_integration)

    integration = fastapi_integration.FastAPIIntegration()
    integration.client = None

    async def run():
        with pytest.raises(RequestValidationError):
            await integration._handle_validation_error(Request(), RequestValidationError("bad"))

        with pytest.raises(StarletteHTTPException):
            await integration._handle_http_exception(Request(), StarletteHTTPException("boom"))

    asyncio.run(run())
