"""Admin UI module for xrayradar server."""

from fastapi.responses import HTMLResponse

from . import css, js, template


def render_admin_ui(*, email: str) -> HTMLResponse:
    """Render the admin UI HTML page with embedded CSS and JavaScript."""
    html = (
        template.HTML_TEMPLATE
        .replace("__CSS__", css.CSS)
        .replace("__JS__", js.JS)
        .replace("__EMAIL__", email)
    )
    return HTMLResponse(html, status_code=200)
