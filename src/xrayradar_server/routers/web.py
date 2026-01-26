import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException


def _get_web_dist_dir() -> Path:
    raw = (os.getenv("XRAYRADAR_WEB_DIST") or "").strip()
    if raw:
        return Path(raw)
    return (Path(__file__).resolve().parents[3] / "xrayradar-web" / "dist")


# Track which apps have had root route registered
_registered_apps = set()

def register_web(app: FastAPI, register_catch_all: bool = True) -> None:
    web_dist_dir = _get_web_dist_dir()
    web_index = web_dist_dir / "index.html"

    # Always register assets mount if it exists (mounts can be safely re-registered)
    if web_index.exists():
        assets_dir = web_dist_dir / "assets"
        if assets_dir.exists():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="web-assets",
            )

    # Only register root route once per app instance
    if id(app) not in _registered_apps:
        @app.get("/", include_in_schema=False)
        def web_root():
            if web_index.exists():
                return FileResponse(str(web_index))
            raise HTTPException(status_code=404, detail="Not Found")
        
        _registered_apps.add(id(app))
    
    # Only register catch-all if requested (should be called after server routes)
    if not register_catch_all:
        return

    def _should_spa_fallback(path: str) -> bool:
        """Check if path should fall back to SPA index.html.
        
        Returns True for client routes that should serve the SPA.
        Returns False for server routes, WordPress paths, and assets (which are mounted).
        """
        # FastAPI {path:path} captures without leading slash, so normalize
        normalized_path = "/" + path if path and not path.startswith("/") else (path or "/")
        
        if normalized_path == "/":
            return True
        
        # Assets are mounted separately, so they shouldn't reach here
        # But if they do, don't serve SPA for them
        if normalized_path.startswith("/assets/"):
            return False
        
        # Block WordPress and other suspicious paths
        if (normalized_path.startswith("/wp-") or 
            normalized_path.startswith("/wp/") or 
            normalized_path.startswith("/wordpress") or
            normalized_path == "/index.php" or
            normalized_path.startswith("/index.php/") or
            "/wp-admin" in normalized_path or
            "wp-admin" in normalized_path):
            return False
        
        # Don't handle API, auth, and other server routes - let FastAPI handle them
        # These will be matched by their actual route handlers before this catch-all
        if normalized_path.startswith("/api/") or normalized_path.startswith("/auth/"):
            return False
        
        # Server routes like /admin, /health, /docs are handled by their actual routes
        # Don't intercept them here
        server_routes = {"/docs", "/redoc", "/openapi.json", "/admin", "/health"}
        if normalized_path in server_routes:
            return False
        
        # Allow all other client-side routes to fall back to SPA
        # This includes /pricing, /some-client-route, etc.
        return True

    @app.get("/{path:path}", include_in_schema=False)
    def handle_spa_routes(path: str, request: Request):
        if _should_spa_fallback(path):
            if web_index.exists():
                return FileResponse(str(web_index))
        
        # Block WordPress and other blocked paths
        raise HTTPException(status_code=404, detail="Not Found")
