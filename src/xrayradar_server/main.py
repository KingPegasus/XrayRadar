from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
import secrets
from urllib.parse import urlencode
from uuid import UUID

import httpx

from fastapi import Depends, FastAPI, HTTPException, Header, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .models import Event, Project, Token, TokenProjectAccess
from .schemas import (
    EventOut,
    ProjectCreate,
    ProjectOut,
    TokenCreate,
    TokenCreateOut,
    TokenOut,
    TokenProjectAccessOut,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="xrayradar-server", lifespan=lifespan)


def _is_production() -> bool:
    return (os.getenv("XRAYRADAR_ENV") or "").strip().lower() == "production"


def _cookie_secure() -> bool:
    raw = (os.getenv("XRAYRADAR_COOKIE_SECURE") or "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return _is_production()


def _get_session_serializer() -> URLSafeSerializer:
    secret = (os.getenv("XRAYRADAR_SESSION_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("XRAYRADAR_SESSION_SECRET is not set")
    return URLSafeSerializer(secret_key=secret, salt="xrayradar-session")


def _parse_admin_allowlist() -> set[str]:
    raw = (os.getenv("XRAYRADAR_ADMIN_EMAILS") or "").strip()
    if not raw:
        return set()
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _get_session_email(request: Request) -> str | None:
    cookie = (request.cookies.get("xrayradar_session") or "").strip()
    if not cookie:
        return None
    s = _get_session_serializer()
    try:
        payload = s.loads(cookie)
    except BadSignature:
        return None
    email = (payload.get("email") if isinstance(payload, dict) else None) or ""
    email = email.strip().lower()
    return email or None


def _is_session_admin(request: Request) -> bool:
    email = _get_session_email(request)
    if not email:
        return False
    allowlist = _parse_admin_allowlist()
    return bool(allowlist) and email in allowlist


def _unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def _forbidden(detail: str = "Forbidden") -> HTTPException:
    return HTTPException(status_code=403, detail=detail)


def get_current_token(
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
) -> Token:
    token_value = (x_xrayradar_token or "").strip()
    if not token_value:
        raise _unauthorized("Missing token")

    q = select(Token).where(Token.token == token_value)
    row = db.execute(q).scalars().first()
    if row is None:
        raise _unauthorized("Invalid token")
    if row.revoked_at is not None:
        raise _unauthorized("Token revoked")
    return row


def require_project_access(
    project_id: int,
    db: Session = Depends(get_db),
    token: Token = Depends(get_current_token),
) -> Token:
    if token.is_admin:
        return token

    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token.id)
        .where(TokenProjectAccess.project_id == project_id)
        .where(TokenProjectAccess.revoked_at.is_(None))
    )
    access = db.execute(q).scalars().first()
    if access is None:
        raise _forbidden("Token has no access to this project")
    return token


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
) -> Token:
    if _is_session_admin(request):
        email = _get_session_email(request) or "admin"
        return Token(name=email, token="", is_admin=True)

    token = get_current_token(db=db, x_xrayradar_token=x_xrayradar_token)
    if token.is_admin:
        return token
    raise _forbidden("Admin privileges required")


@app.get("/auth/github/login")
def github_login() -> RedirectResponse:
    client_id = (os.getenv("XRAYRADAR_GITHUB_CLIENT_ID") or "").strip()
    redirect_uri = (os.getenv("XRAYRADAR_GITHUB_REDIRECT_URI") or "").strip()
    if not client_id or not redirect_uri:
        raise HTTPException(
            status_code=500, detail="GitHub OAuth is not configured")

    state = secrets.token_urlsafe(24)
    s = _get_session_serializer()
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
        secure=_cookie_secure(),
        path="/",
        max_age=600,
    )
    return resp


@app.get("/auth/github/callback")
def github_callback(request: Request, code: str | None = None, state: str | None = None) -> RedirectResponse:
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code/state")

    s = _get_session_serializer()
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

    token_url = "https://github.com/login/oauth/access_token"
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
            "User-Agent": "xrayradar-server",
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

    allowlist = _parse_admin_allowlist()
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
        secure=_cookie_secure(),
        path="/",
        max_age=60 * 60 * 12,
    )
    return resp


@app.post("/auth/logout")
def logout(_: Request, response: Response) -> dict:
    response.delete_cookie("xrayradar_session", path="/")
    return {"ok": True}


@app.get("/admin", response_class=HTMLResponse)
def admin_ui(request: Request) -> HTMLResponse:
    if not _is_session_admin(request):
        return HTMLResponse(
            '<html><body><a href="/auth/github/login">Login with GitHub</a></body></html>',
            status_code=401,
        )
    email = _get_session_email(request) or ""
    html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>xrayradar admin</title>
    <style>
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; margin: 0; background: #0b1220; color: #e5e7eb; }
      header { padding: 16px 20px; border-bottom: 1px solid #1f2937; display: flex; justify-content: space-between; align-items: center; }
      header .title { font-weight: 700; letter-spacing: 0.2px; }
      header .meta { opacity: 0.9; font-size: 13px; }
      main { padding: 16px 20px; display: grid; grid-template-columns: 420px 1fr; gap: 16px; }
      section { background: #0f172a; border: 1px solid #1f2937; border-radius: 10px; padding: 14px; }
      h2 { margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: #cbd5e1; }
      label { display: block; margin: 10px 0 6px; font-size: 12px; color: #cbd5e1; }
      input, select { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0b1220; color: #e5e7eb; }
      input::placeholder { color: #64748b; }
      button { padding: 10px 12px; border-radius: 8px; border: 1px solid #334155; background: #111827; color: #e5e7eb; cursor: pointer; }
      button.primary { background: #2563eb; border-color: #2563eb; }
      button.danger { background: #b91c1c; border-color: #b91c1c; }
      button.small { padding: 6px 10px; font-size: 12px; }
      button:disabled { opacity: 0.5; cursor: not-allowed; }
      .row { display: flex; gap: 10px; }
      .row > * { flex: 1; }
      .muted { color: #94a3b8; font-size: 12px; }
      .error { color: #fca5a5; font-size: 12px; white-space: pre-wrap; }
      .ok { color: #86efac; font-size: 12px; white-space: pre-wrap; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid #1f2937; padding: 8px; font-size: 13px; text-align: left; vertical-align: top; }
      th { color: #cbd5e1; font-weight: 600; }
      tr:hover td { background: rgba(148, 163, 184, 0.06); }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid #334155; color: #cbd5e1; }
      .pill.admin { border-color: #2563eb; color: #93c5fd; }
      .pill.revoked { border-color: #b91c1c; color: #fca5a5; }
      a { color: #93c5fd; }
      .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 10px; }
    </style>
  </head>
  <body>
    <header>
      <div>
        <div class="title">xrayradar admin</div>
        <div class="meta">Logged in as <span id="who">__EMAIL__</span></div>
      </div>
      <div class="row" style="max-width: 320px">
        <button id="refresh" class="small">Refresh</button>
        <button id="logout" class="small danger">Logout</button>
      </div>
    </header>

    <main>
      <section>
        <h2>Create token</h2>
        <div class=\"muted\">Create a token tied to an email/name. Grant project access from the right panel.</div>

        <label>Name</label>
        <input id=\"t_name\" placeholder=\"app-ingest\" />

        <label>Email (optional)</label>
        <input id=\"t_email\" placeholder=\"owner@example.com\" />

        <label>Admin</label>
        <select id=\"t_admin\">
          <option value=\"false\" selected>False</option>
          <option value=\"true\">True</option>
        </select>

        <div style=\"margin-top: 12px\" class=\"row\">
          <button id=\"create\" class=\"primary\">Create</button>
        </div>

        <div id=\"create_out\" class=\"ok\" style=\"margin-top: 10px\"></div>
        <div id=\"create_err\" class=\"error\" style=\"margin-top: 10px\"></div>

        <hr style=\"border: 0; border-top: 1px solid #1f2937; margin: 14px 0\" />

        <h2>Tokens</h2>
        <div class=\"muted\">Click a token to manage its project access.</div>
        <div style=\"margin-top: 10px\">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody id=\"tokens\"></tbody>
          </table>
        </div>
      </section>

      <section>
        <div class=\"toolbar\">
          <div>
            <h2 style=\"margin-bottom: 4px\">Token access</h2>
            <div class=\"muted\">Selected token: <span id=\"selected\">(none)</span></div>
          </div>
          <button id=\"revoke_token\" class=\"small danger\" disabled>Revoke token</button>
        </div>

        <div id=\"access_err\" class=\"error\" style=\"margin: 8px 0\"></div>

        <div class=\"row\" style=\"align-items: flex-end\">
          <div>
            <label>Project</label>
            <select id=\"projects\"></select>
          </div>
          <div>
            <button id=\"grant\" class=\"primary\" disabled>Grant</button>
          </div>
        </div>

        <div style=\"margin-top: 12px\">
          <table>
            <thead>
              <tr>
                <th>Access ID</th>
                <th>Project ID</th>
                <th>Created</th>
                <th>Revoked</th>
                <th></th>
              </tr>
            </thead>
            <tbody id=\"grants\"></tbody>
          </table>
        </div>
      </section>
    </main>

    <script>
      const state = {
        tokens: [],
        projects: [],
        selectedTokenId: null,
      };

      function qs(id) { return document.getElementById(id); }

      function showErr(el, msg) { el.textContent = msg || ""; }

      async function api(path, opts={}) {
        const r = await fetch(path, Object.assign({ credentials: 'same-origin' }, opts));
        const text = await r.text();
        let data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
        if (!r.ok) {
          const detail = (data && data.detail) ? data.detail : (typeof data === 'string' ? data : r.statusText);
          throw new Error(`HTTP ${r.status}: ${detail}`);
        }
        return data;
      }

      function renderProjects() {
        const sel = qs('projects');
        sel.innerHTML = '';
        for (const p of state.projects) {
          const opt = document.createElement('option');
          opt.value = String(p.id);
          opt.textContent = `${p.id} - ${p.name}`;
          sel.appendChild(opt);
        }
      }

      function renderTokens() {
        const tbody = qs('tokens');
        tbody.innerHTML = '';
        for (const t of state.tokens) {
          const tr = document.createElement('tr');
          tr.style.cursor = 'pointer';
          tr.addEventListener('click', () => selectToken(t.id));
          const flags = [];
          if (t.is_admin) flags.push('<span class="pill admin">admin</span>');
          if (t.revoked_at) flags.push('<span class="pill revoked">revoked</span>');
          tr.innerHTML = `
            <td>${t.id}</td>
            <td>${escapeHtml(t.name || '')}</td>
            <td>${escapeHtml(t.email || '')}</td>
            <td>${flags.join(' ')}</td>
          `;
          tbody.appendChild(tr);
        }
      }

      function escapeHtml(s) {
        return String(s)
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;')
          .replaceAll('"', '&quot;')
          .replaceAll("'", '&#039;');
      }

      async function selectToken(tokenId) {
        state.selectedTokenId = tokenId;
        qs('selected').textContent = String(tokenId);
        qs('grant').disabled = false;
        qs('revoke_token').disabled = false;
        await refreshGrants();
      }

      async function refreshGrants() {
        showErr(qs('access_err'), '');
        const tbody = qs('grants');
        tbody.innerHTML = '';
        if (!state.selectedTokenId) return;

        try {
          const grants = await api(`/api/admin/tokens/${state.selectedTokenId}/projects`);
          for (const g of grants) {
            const tr = document.createElement('tr');
            const revoked = g.revoked_at ? escapeHtml(g.revoked_at) : '';
            const btn = document.createElement('button');
            btn.className = 'small';
            btn.textContent = g.revoked_at ? 'Revoked' : 'Revoke';
            btn.disabled = !!g.revoked_at;
            btn.addEventListener('click', async () => {
              await revokeGrant(g.project_id);
            });
            tr.innerHTML = `
              <td>${g.id}</td>
              <td>${g.project_id}</td>
              <td>${escapeHtml(g.created_at)}</td>
              <td>${revoked}</td>
              <td></td>
            `;
            tr.children[4].appendChild(btn);
            tbody.appendChild(tr);
          }
        } catch (e) {
          showErr(qs('access_err'), e.message);
        }
      }

      async function grantSelected() {
        showErr(qs('access_err'), '');
        if (!state.selectedTokenId) return;
        const projectId = Number(qs('projects').value);
        try {
          await api(`/api/admin/tokens/${state.selectedTokenId}/projects/${projectId}/grant`, { method: 'POST' });
          await refreshGrants();
        } catch (e) {
          showErr(qs('access_err'), e.message);
        }
      }

      async function revokeGrant(projectId) {
        showErr(qs('access_err'), '');
        if (!state.selectedTokenId) return;
        try {
          await api(`/api/admin/tokens/${state.selectedTokenId}/projects/${projectId}/revoke`, { method: 'POST' });
          await refreshGrants();
        } catch (e) {
          showErr(qs('access_err'), e.message);
        }
      }

      async function revokeToken() {
        showErr(qs('access_err'), '');
        if (!state.selectedTokenId) return;
        try {
          await api(`/api/admin/tokens/${state.selectedTokenId}/revoke`, { method: 'POST' });
          await loadAll();
        } catch (e) {
          showErr(qs('access_err'), e.message);
        }
      }

      async function createToken() {
        showErr(qs('create_err'), '');
        qs('create_out').textContent = '';

        const name = qs('t_name').value.trim();
        const email = qs('t_email').value.trim();
        const is_admin = qs('t_admin').value === 'true';
        if (!name) {
          showErr(qs('create_err'), 'Name is required');
          return;
        }

        try {
          const out = await api('/api/admin/tokens', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email: email || null, is_admin }),
          });
          qs('create_out').textContent = `Created token id=${out.id}. Token value (copy now): ${out.token}`;
          qs('t_name').value = '';
          qs('t_email').value = '';
          qs('t_admin').value = 'false';
          await loadAll();
        } catch (e) {
          showErr(qs('create_err'), e.message);
        }
      }

      async function loadAll() {
        showErr(qs('create_err'), '');
        showErr(qs('access_err'), '');

        state.projects = await api('/api/admin/projects');
        state.tokens = await api('/api/admin/tokens');

        renderProjects();
        renderTokens();

        if (state.selectedTokenId) {
          const exists = state.tokens.some(t => t.id === state.selectedTokenId);
          if (!exists) {
            state.selectedTokenId = null;
            qs('selected').textContent = '(none)';
            qs('grant').disabled = true;
            qs('revoke_token').disabled = true;
            qs('grants').innerHTML = '';
          } else {
            await refreshGrants();
          }
        }
      }

      async function doLogout() {
        await api('/auth/logout', { method: 'POST' });
        window.location.href = '/admin';
      }

      qs('create').addEventListener('click', createToken);
      qs('grant').addEventListener('click', grantSelected);
      qs('revoke_token').addEventListener('click', revokeToken);
      qs('refresh').addEventListener('click', loadAll);
      qs('logout').addEventListener('click', doLogout);

      loadAll().catch(e => {
        showErr(qs('access_err'), e.message);
      });
    </script>
  </body>
</html>"""

    html = html.replace("__EMAIL__", email)

    return HTMLResponse(html, status_code=200)


@app.get("/api/admin/me", response_model=dict)
def admin_me(request: Request) -> dict:
    if not _is_session_admin(request):
        raise _unauthorized("Not logged in")
    return {"email": _get_session_email(request)}


def authorize_ingest_for_project(
    *,
    project_id: int,
    db: Session,
    x_xrayradar_token: str | None,
) -> None:
    token = get_current_token(db=db, x_xrayradar_token=x_xrayradar_token)
    require_project_access(project_id=project_id, db=db, token=token)


@app.get("/health", response_model=dict)
def health() -> dict:
    return {
        "status": "ok",
        "auth_required": True,
    }


@app.post("/api/projects", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    project = Project(name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(id=project.id, name=project.name)


@app.post("/api/{project_id}/store/", response_model=dict)
def store_event(
    project_id: int,
    event: dict,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
):
    authorize_ingest_for_project(
        project_id=project_id,
        db=db,
        x_xrayradar_token=x_xrayradar_token,
    )

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

    # SDK sends event_id + timestamp, but be defensive
    event_id = event.get("event_id")
    timestamp = event.get("timestamp")
    level = event.get("level") or "error"
    message = event.get("message") or ""

    try:
        ts = datetime.fromisoformat(timestamp.replace(
            "Z", "+00:00")) if isinstance(timestamp, str) else datetime.now(timezone.utc)
    except Exception:
        ts = datetime.now(timezone.utc)

    env = (event.get("contexts") or {}).get("environment")
    rel = (event.get("contexts") or {}).get("release")
    server_name = (event.get("contexts") or {}).get("server_name")

    row = Event(
        project_id=project_id,
        timestamp=ts,
        level=str(level),
        message=str(message)[:2048],
        environment=env,
        release=rel,
        server_name=server_name,
        payload=event,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return {"id": str(row.id)}


@app.get("/api/{project_id}/events", response_model=list[EventOut])
def list_events(
    project_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Token = Depends(require_project_access),
):
    q = (
        select(Event)
        .where(Event.project_id == project_id)
        .order_by(Event.timestamp.desc())
        .limit(min(max(limit, 1), 200))
    )
    rows = db.execute(q).scalars().all()
    return [
        EventOut(
            id=r.id,
            project_id=r.project_id,
            timestamp=r.timestamp,
            level=r.level,
            message=r.message,
            payload=r.payload,
        )
        for r in rows
    ]


@app.get("/api/{project_id}/events/{event_id}", response_model=EventOut)
def get_event(
    project_id: int,
    event_id: UUID,
    db: Session = Depends(get_db),
    _: Token = Depends(require_project_access),
):
    row = db.get(Event, event_id)
    if row is None or row.project_id != project_id:
        raise HTTPException(status_code=404, detail="Not found")
    return EventOut(
        id=row.id,
        project_id=row.project_id,
        timestamp=row.timestamp,
        level=row.level,
        message=row.message,
        payload=row.payload,
    )


@app.post("/api/admin/tokens", response_model=TokenCreateOut)
def admin_create_token(
    payload: TokenCreate,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    token_value = secrets.token_urlsafe(32)
    row = Token(
        name=payload.name,
        email=(payload.email or "").strip().lower() or None,
        token=token_value,
        is_admin=payload.is_admin,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TokenCreateOut(
        id=row.id,
        name=row.name,
        email=row.email,
        is_admin=row.is_admin,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
        token=row.token,
    )


@app.get("/api/admin/tokens", response_model=list[TokenOut])
def admin_list_tokens(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    q = select(Token).order_by(Token.id.asc())
    rows = db.execute(q).scalars().all()
    return [
        TokenOut(
            id=r.id,
            name=r.name,
            email=r.email,
            is_admin=r.is_admin,
            created_at=r.created_at,
            revoked_at=r.revoked_at,
        )
        for r in rows
    ]


@app.post("/api/admin/tokens/{token_id}/revoke", response_model=TokenOut)
def admin_revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    row = db.get(Token, token_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
    return TokenOut(
        id=row.id,
        name=row.name,
        email=row.email,
        is_admin=row.is_admin,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
    )


@app.get("/api/admin/projects", response_model=list[ProjectOut])
def admin_list_projects(db: Session = Depends(get_db), _: Token = Depends(require_admin)):
    q = select(Project).order_by(Project.id.asc())
    rows = db.execute(q).scalars().all()
    return [ProjectOut(id=p.id, name=p.name) for p in rows]


@app.post(
    "/api/admin/tokens/{token_id}/projects/{project_id}/grant",
    response_model=TokenProjectAccessOut,
)
def admin_grant_project_access(
    token_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    token_row = db.get(Token, token_id)
    if token_row is None:
        raise HTTPException(status_code=404, detail="Token not found")
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")

    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
        .where(TokenProjectAccess.project_id == project_id)
        .order_by(TokenProjectAccess.id.desc())
    )
    access = db.execute(q).scalars().first()
    if access is None:
        access = TokenProjectAccess(token_id=token_id, project_id=project_id)
    else:
        access.revoked_at = None

    db.add(access)
    db.commit()
    db.refresh(access)
    return TokenProjectAccessOut(
        id=access.id,
        token_id=access.token_id,
        project_id=access.project_id,
        created_at=access.created_at,
        revoked_at=access.revoked_at,
    )


@app.post(
    "/api/admin/tokens/{token_id}/projects/{project_id}/revoke",
    response_model=TokenProjectAccessOut,
)
def admin_revoke_project_access(
    token_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
        .where(TokenProjectAccess.project_id == project_id)
        .where(TokenProjectAccess.revoked_at.is_(None))
        .order_by(TokenProjectAccess.id.desc())
    )
    access = db.execute(q).scalars().first()
    if access is None:
        raise HTTPException(status_code=404, detail="Access not found")

    access.revoked_at = datetime.now(timezone.utc)
    db.add(access)
    db.commit()
    db.refresh(access)
    return TokenProjectAccessOut(
        id=access.id,
        token_id=access.token_id,
        project_id=access.project_id,
        created_at=access.created_at,
        revoked_at=access.revoked_at,
    )


@app.get(
    "/api/admin/tokens/{token_id}/projects",
    response_model=list[TokenProjectAccessOut],
)
def admin_list_token_projects(
    token_id: int,
    db: Session = Depends(get_db),
    _: Token = Depends(require_admin),
):
    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token_id)
        .order_by(TokenProjectAccess.project_id.asc())
    )
    rows = db.execute(q).scalars().all()
    return [
        TokenProjectAccessOut(
            id=r.id,
            token_id=r.token_id,
            project_id=r.project_id,
            created_at=r.created_at,
            revoked_at=r.revoked_at,
        )
        for r in rows
    ]
