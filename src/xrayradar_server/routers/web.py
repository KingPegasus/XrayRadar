import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse, RedirectResponse
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
        @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
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

    # Root static files (favicon, robots, sitemap, etc.) - serve from dist if present
    _root_static = ("favicon.ico", "robots.txt", "sitemap.xml", "manifest.json", "apple-touch-icon.png", "og-image.webp", "og-image.png", "logo.svg", "logo_square.svg", "xray-logo.png")

    # Legacy URLs that now live as sections of the landing page.
    _legacy_redirects = {"pricing": "/#pricing", "features": "/#features", "sdks": "/#sdks", "faq": "/#faq"}

    # Pre-rendered route pages emitted by the web build (dist/<route>/index.html).
    _route_name = re.compile(r"^[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*$")

    def _is_dashboard(path_name: str) -> bool:
        return path_name == "dashboard" or path_name.startswith("dashboard/")

    def _not_found() -> FileResponse:
        """Real 404 status (avoids soft-404s) with the SPA's not-found page."""
        not_found = web_dist_dir / "404.html"
        return FileResponse(
            str(not_found if not_found.is_file() else web_index),
            status_code=404,
            headers={"X-Robots-Tag": "noindex"},
        )

    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def handle_spa_routes(path: str, request: Request):
        normalized_path = "/" + path if path and not path.startswith("/") else (path or "/")
        path_name = normalized_path.lstrip("/")

        if path_name in _root_static:
            static_file = web_dist_dir / path_name
            if static_file.is_file():
                return FileResponse(str(static_file))

        if not _should_spa_fallback(path) or not web_index.exists():
            # HEAD is registered here only for the SPA; for server/API paths keep
            # the usual "method not allowed" answer instead of a misleading 404.
            if request.method == "HEAD" and web_index.exists():
                raise HTTPException(status_code=405, detail="Method Not Allowed", headers={"Allow": "GET"})
            raise HTTPException(status_code=404, detail="Not Found")

        route = path_name.strip("/")
        if not route or route == "index.html":
            if path_name:
                return RedirectResponse("/", status_code=301)
            return FileResponse(str(web_index))

        # Only well-formed route names are considered; anything else (backslashes,
        # dots, encoded hosts, trailing newlines) is a 404 and is never echoed into a redirect.
        if not _route_name.fullmatch(route) or any(seg in (".", "..") for seg in route.split("/")):
            return _not_found()

        # Route names are lowercase; only the first segment is folded so IDs deeper
        # in dashboard URLs keep their case.
        first, sep, rest = route.partition("/")
        canonical = first.lower() + sep + rest

        # Legacy section URLs go straight to their final target (one hop).
        if canonical in _legacy_redirects:
            return RedirectResponse(_legacy_redirects[canonical], status_code=301)

        # One canonical URL per page: no trailing slash, lowercase.
        if canonical != path_name:
            target = "/" + canonical
            if request.url.query:
                target += "?" + request.url.query
            return RedirectResponse(target, status_code=301)

        # Known public route with pre-rendered SEO head.
        route_file = web_dist_dir / route / "index.html"
        if "." not in route and route_file.is_file():
            return FileResponse(str(route_file))

        # Authenticated app: serve the SPA but keep it out of search results.
        if _is_dashboard(route):
            dashboard = web_dist_dir / "dashboard.html"
            return FileResponse(
                str(dashboard if dashboard.is_file() else web_index),
                headers={"X-Robots-Tag": "noindex"},
            )

        # Builds that predate pre-rendered routes have no 404.html: keep the old
        # behaviour (SPA with 200) so real pages like /reset-password still work.
        if not (web_dist_dir / "404.html").is_file():
            return FileResponse(str(web_index))

        return _not_found()
