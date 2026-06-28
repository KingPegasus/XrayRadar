import asyncio
import contextlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import secrets
from urllib.parse import urlencode

import httpx

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import BadSignature
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .db import init_db
from .rate_limit import limiter
from .admin_ui import render_admin_ui
from .auth import (
    cookie_secure,
    get_session_email,
    get_session_serializer,
    parse_admin_allowlist,
)
from .constants import GITHUB_OAUTH_ACCESS_TOKEN_URL
from .constants import SCHEDULER_ENABLED, SCHEDULER_INTERVAL_SECONDS
from .deps import (
    _is_session_admin,
    admin_me,
    health,
)
from .routers.web import register_web
from .routers import admin_api as admin_api_router
from .routers import api as api_router
from .routers import user as user_api_router
from .routers import user_auth as user_auth_router
from .alert_scheduler import run_once as run_alert_scheduler_once


logger = logging.getLogger(__name__)


async def _scheduler_loop(stop_event: asyncio.Event) -> None:
    interval = max(10, int(SCHEDULER_INTERVAL_SECONDS or 60))
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(run_alert_scheduler_once)
        except Exception as e:  # noqa: BLE001
            logger.warning("In-process alert scheduler run failed: %s", e)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    stop_event = asyncio.Event()
    scheduler_task: asyncio.Task | None = None
    if SCHEDULER_ENABLED:
        scheduler_task = asyncio.create_task(_scheduler_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        if scheduler_task is not None:
            scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await scheduler_task


app = FastAPI(
    title="XrayRadar",
    version="0.19.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    # Disable default /openapi.json (schema not exposed publicly)
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
# CORS so browser apps (e.g. React) on other origins can POST to /api/{project_id}/store/
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register web static files and root route, but not catch-all yet
register_web(app, register_catch_all=False)

app.include_router(user_auth_router.router)
app.include_router(api_router.router)
app.include_router(admin_api_router.router)
app.include_router(user_api_router.router)


@app.get("/auth/github/login")
def github_login() -> RedirectResponse:
    client_id = (os.getenv("XRAYRADAR_GITHUB_CLIENT_ID") or "").strip()
    redirect_uri = (os.getenv("XRAYRADAR_GITHUB_REDIRECT_URI") or "").strip()
    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=500, detail="GitHub OAuth is not configured")

    state = secrets.token_urlsafe(24)
    s = get_session_serializer()
    state_cookie = s.dumps(
        {"state": state, "ts": int(datetime.now(timezone.utc).timestamp())})

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state,
    }
    url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    resp = RedirectResponse(url=url, status_code=302)
    resp.set_cookie(
        "xrayradar_oauth_state",
        state_cookie,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        path="/",
        max_age=600,
    )
    return resp


@app.get("/auth/github/callback")
def github_callback(request: Request, code: str | None = None, state: str | None = None) -> RedirectResponse:
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    s = get_session_serializer()
    raw_cookie = (request.cookies.get("xrayradar_oauth_state") or "").strip()
    if not raw_cookie:
        raise HTTPException(
            status_code=400, detail="Missing oauth state cookie")
    try:
        cookie_payload = s.loads(raw_cookie)
    except BadSignature:
        raise HTTPException(
            status_code=400, detail="Invalid oauth state cookie")
    expected_state = (cookie_payload.get("state") if isinstance(
        cookie_payload, dict) else None) or ""
    if expected_state != state:
        raise HTTPException(status_code=400, detail="Invalid oauth state")

    client_id = (os.getenv("XRAYRADAR_GITHUB_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("XRAYRADAR_GITHUB_CLIENT_SECRET") or "").strip()
    redirect_uri = (os.getenv("XRAYRADAR_GITHUB_REDIRECT_URI") or "").strip()
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=500, detail="GitHub OAuth is not configured")

    token_url = GITHUB_OAUTH_ACCESS_TOKEN_URL
    async_headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    with httpx.Client(timeout=10.0) as client:
        r = client.post(token_url, data=data, headers=async_headers)
        if r.status_code >= 400:
            raise HTTPException(
                status_code=502, detail="GitHub token exchange failed")
        token_payload = r.json()
        access_token = (token_payload.get("access_token") or "").strip()
        if not access_token:
            raise HTTPException(
                status_code=502, detail="Missing GitHub access token")

        api_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "XrayRadar",
        }

        emails = client.get(
            "https://api.github.com/user/emails", headers=api_headers)
        if emails.status_code >= 400:
            raise HTTPException(
                status_code=502, detail="Failed to fetch GitHub emails")
        emails_payload = emails.json() if isinstance(emails.json(), list) else []

    chosen = ""
    for e in emails_payload:
        if isinstance(e, dict) and e.get("primary") and e.get("verified") and e.get("email"):
            chosen = str(e.get("email"))
            break
    if not chosen:
        for e in emails_payload:
            if isinstance(e, dict) and e.get("verified") and e.get("email"):
                chosen = str(e.get("email"))
                break

    email = chosen.strip().lower()
    if not email:
        raise HTTPException(status_code=403, detail="No verified email found")

    allowlist = parse_admin_allowlist()
    if not allowlist or email not in allowlist:
        raise HTTPException(status_code=403, detail=f"Not allowed for {email}")

    session_cookie = s.dumps(
        {"email": email, "ts": int(datetime.now(timezone.utc).timestamp())})
    resp = RedirectResponse(url="/admin", status_code=302)
    resp.delete_cookie("xrayradar_oauth_state", path="/")
    resp.set_cookie(
        "xrayradar_session",
        session_cookie,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        path="/",
        max_age=60 * 60 * 12,
    )
    return resp


@app.get("/admin", response_class=HTMLResponse)
def admin_ui(request: Request) -> HTMLResponse:
    if not _is_session_admin(request):
        return HTMLResponse(
            '<html><body><a href="/auth/github/login">Login with GitHub</a></body></html>',
            status_code=401,
        )
    email = get_session_email(request) or ""
    return render_admin_ui(email=email)


@app.get("/openapi.json", response_class=JSONResponse, include_in_schema=False)
def openapi_schema(request: Request) -> JSONResponse:
    """OpenAPI schema (admin only). Used by /docs and /redoc to render the API reference."""
    if not _is_session_admin(request):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin authentication required.",
        )
    return JSONResponse(app.openapi())


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
def custom_swagger_ui(request: Request) -> HTMLResponse:
    """Protected Swagger UI - only accessible to admins."""
    if not _is_session_admin(request):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin authentication required.",
        )
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
    )


@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
def custom_redoc(request: Request) -> HTMLResponse:
    """Protected ReDoc - only accessible to admins."""
    if not _is_session_admin(request):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin authentication required.",
        )
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
    )


@app.get("/api/admin/me", response_model=dict)
def admin_me_endpoint(request: Request) -> dict:
    return admin_me(request)


@app.get("/health", response_model=dict)
def health_endpoint() -> dict:
    return health()


# Register catch-all route for SPA AFTER all server routes are defined
# This ensures server routes like /admin, /health are matched first
register_web(app, register_catch_all=True)


# Backward-compatible re-exports for tests that call mainmod.* directly.
logout = user_auth_router.logout
admin_grant_project_access = admin_api_router.admin_grant_project_access
admin_revoke_project_access = admin_api_router.admin_revoke_project_access
admin_list_token_projects = admin_api_router.admin_list_token_projects
