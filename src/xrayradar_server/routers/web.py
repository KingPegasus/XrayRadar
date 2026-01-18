import os
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


def register_web(app: FastAPI) -> None:
    web_dist_dir = _get_web_dist_dir()
    web_index = web_dist_dir / "index.html"

    if web_index.exists():
        assets_dir = web_dist_dir / "assets"
        if assets_dir.exists():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="web-assets",
            )

    @app.get("/", include_in_schema=False)
    def web_root():
        if web_index.exists():
            return FileResponse(str(web_index))
        raise HTTPException(status_code=404, detail="Not Found")

    def _should_spa_fallback(path: str) -> bool:
        if not web_index.exists():
            return False

        path = (path or "").lstrip("/")
        if not path:
            return False

        if path.startswith("api/"):
            return False
        if path.startswith("auth/"):
            return False
        if path.startswith("assets/"):
            return False
        if path in {"docs", "redoc", "openapi.json", "admin", "health"}:
            return False

        return True

    @app.exception_handler(StarletteHTTPException)
    async def spa_404_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404 and _should_spa_fallback(request.url.path):
            return FileResponse(str(web_index))
        return await http_exception_handler(request, exc)
