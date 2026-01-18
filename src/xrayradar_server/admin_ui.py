from fastapi.responses import HTMLResponse


def render_admin_ui(*, email: str) -> HTMLResponse:
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
        <div class="muted">Create a token tied to an email/name. Grant project access from the right panel.</div>

        <label>Name</label>
        <input id="t_name" placeholder="app-ingest" />

        <label>Email (optional)</label>
        <input id="t_email" placeholder="owner@example.com" />

        <label>Admin</label>
        <select id="t_admin">
          <option value="false" selected>False</option>
          <option value="true">True</option>
        </select>

        <div style="margin-top: 12px" class="row">
          <button id="create" class="primary">Create</button>
        </div>

        <div id="create_out" class="ok" style="margin-top: 10px"></div>
        <div id="create_err" class="error" style="margin-top: 10px"></div>

        <hr style="border: 0; border-top: 1px solid #1f2937; margin: 14px 0" />

        <h2>Tokens</h2>
        <div class="muted">Click a token to manage its project access.</div>
        <div style="margin-top: 10px">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody id="tokens"></tbody>
          </table>
        </div>
      </section>

      <section>
        <div class="toolbar">
          <div>
            <h2 style="margin-bottom: 4px">Token access</h2>
            <div class="muted">Selected token: <span id="selected">(none)</span></div>
          </div>
          <button id="revoke_token" class="small danger" disabled>Revoke token</button>
        </div>

        <div id="access_err" class="error" style="margin: 8px 0"></div>

        <div class="row" style="align-items: flex-end">
          <div>
            <label>Project</label>
            <select id="projects"></select>
          </div>
          <div>
            <button id="grant" class="primary" disabled>Grant</button>
          </div>
        </div>

        <div style="margin-top: 12px">
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
            <tbody id="grants"></tbody>
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
