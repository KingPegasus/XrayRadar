import asyncio

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
