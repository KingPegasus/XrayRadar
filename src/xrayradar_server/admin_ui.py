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
      .layout { display: grid; grid-template-columns: 240px 1fr; min-height: calc(100vh - 66px); }
      aside { border-right: 1px solid #1f2937; background: rgba(15, 23, 42, 0.4); }
      .sideInner { padding: 14px 12px; }
      .navItem { display: flex; align-items: center; gap: 10px; padding: 10px 10px; border-radius: 10px; cursor: pointer; color: #cbd5e1; border: 1px solid transparent; }
      .navItem:hover { background: rgba(148, 163, 184, 0.08); }
      .navItem.active { background: rgba(37, 99, 235, 0.18); border-color: rgba(37, 99, 235, 0.35); color: #e5e7eb; }
      .navDot { width: 9px; height: 9px; border-radius: 999px; background: #334155; }
      .navItem.active .navDot { background: #2563eb; }
      .content { padding: 16px 20px; }
      .view { display: block; }
      .hidden { display: none !important; }
      .grid2 { display: grid; grid-template-columns: 420px 1fr; gap: 16px; }
      @media (max-width: 1000px) {
        .layout { grid-template-columns: 1fr; }
        aside { border-right: 0; border-bottom: 1px solid #1f2937; }
        .sideInner { display: flex; gap: 10px; flex-wrap: wrap; }
        .grid2 { grid-template-columns: 1fr; }
      }
      section { background: #0f172a; border: 1px solid #1f2937; border-radius: 10px; padding: 14px; }
      h2 { margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: #cbd5e1; }
      label { display: block; margin: 10px 0 6px; font-size: 12px; color: #cbd5e1; }
      input, select { width: 90%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0b1220; color: #e5e7eb; }
      input::placeholder { color: #64748b; }
      button { padding: 10px 12px; border-radius: 8px; border: 1px solid #334155; background: #111827; color: #e5e7eb; cursor: pointer; }
      button.primary { background: #2563eb; border-color: #2563eb; }
      button.danger { background: #b91c1c; border-color: #b91c1c; }
      button.small { padding: 6px 10px; font-size: 12px; }
      button:disabled { opacity: 0.5; cursor: not-allowed; }
      .row { display: flex; gap: 10px; flex-wrap: wrap; }
      .row > * { flex: 1; min-width: 180px; }
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
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
      .codeblock { white-space: pre; overflow: auto; margin: 0; padding: 12px; border-radius: 10px; border: 1px solid #1f2937; background: rgba(0, 0, 0, 0.22); color: #e5e7eb; font-size: 12px; line-height: 1.45; }

      .modalOverlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.64); display: grid; place-items: center; padding: 16px; z-index: 50; }
      .modalCard { width: min(980px, 100%); max-height: min(86vh, 900px); overflow: hidden; display: grid; grid-template-rows: auto 1fr; }
      .modalHeader { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #1f2937; background: rgba(15, 23, 42, 0.85); }
      .modalBody { padding: 14px; overflow: auto; }
      .modalTitle { font-weight: 800; letter-spacing: 0.2px; }
      .modalClose { width: 34px; height: 34px; padding: 0; border-radius: 10px; display: grid; place-items: center; }
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

    <div class="layout">
      <aside>
        <div class="sideInner">
          <div class="navItem" data-view="tokens" role="link" tabindex="0">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Tokens</div>
              <div class="muted" style="margin-top: 2px">Create and manage access</div>
            </div>
          </div>
          <div class="navItem" data-view="logs" role="link" tabindex="0" style="margin-top: 8px">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Project logs</div>
              <div class="muted" style="margin-top: 2px">Browse stored events</div>
            </div>
          </div>
        </div>
      </aside>

      <div class="content">
        <div id="view_tokens" class="view">
          <div class="grid2">
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
          </div>
        </div>

        <div id="view_logs" class="view hidden">
          <section>
            <h2>Project logs</h2>
            <div class="muted">Browse raw stored events per project, with lightweight filtering and event payload viewing.</div>

            <div class="row" style="margin-top: 12px; align-items: flex-end">
              <div style="flex: 0.8; min-width: 140px">
                <label>Project</label>
                <select id="logs_project"></select>
              </div>
              <div style="flex: 0.8; min-width: 140px">
                <label>Level</label>
                <select id="logs_level">
                  <option value="" selected>(any)</option>
                  <option value="error">error</option>
                  <option value="warning">warning</option>
                  <option value="info">info</option>
                  <option value="debug">debug</option>
                </select>
              </div>
              <div style="flex: 0.8; min-width: 140px">
                <label>Environment</label>
                <input id="logs_env" placeholder="production" />
              </div>
              <div style="flex: 0.8; min-width: 140px">
                <label>Release</label>
                <input id="logs_release" placeholder="1.2.3" />
              </div>
            </div>

            <div class="row" style="margin-top: 10px; align-items: flex-end">
              <div style="flex: 2">
                <label>Search message</label>
                <input id="logs_q" placeholder="contains..." />
              </div>
              <div style="flex: 0.8">
                <button id="logs_load" class="primary">Load</button>
              </div>
              <div style="flex: 0.8">
                <button id="logs_more" disabled>Load more</button>
              </div>
            </div>

            <div id="logs_err" class="error" style="margin-top: 10px"></div>
          </section>

          <section style="margin-top: 16px">
            <div class="muted" style="margin-bottom: 10px">Tip: click a row to view full JSON payload.</div>
            <table>
              <thead>
                <tr>
                  <th style="width: 180px">Time</th>
                  <th style="width: 90px">Level</th>
                  <th style="width: 160px">Environment</th>
                  <th style="width: 160px">Release</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody id="logs_rows"></tbody>
            </table>
          </section>

          <div id="logs_modal" class="modalOverlay hidden" role="dialog" aria-modal="true" aria-label="Event detail">
            <div class="modalCard" style="background: #0f172a; border: 1px solid #1f2937; border-radius: 12px">
              <div class="modalHeader">
                <div style="min-width: 0">
                  <div class="modalTitle">Event detail</div>
                  <div class="muted" style="margin-top: 4px">
                    <span id="logs_modal_meta" class="mono"></span>
                  </div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center">
                  <button id="logs_copy" class="small">Copy JSON</button>
                  <button id="logs_modal_close" class="modalClose small">×</button>
                </div>
              </div>
              <div class="modalBody">
                <div id="logs_modal_msg" class="ok" style="margin-bottom: 10px"></div>
                <pre id="logs_payload" class="codeblock mono"></pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      const state = {
        tokens: [],
        projects: [],
        selectedTokenId: null,
        view: 'tokens',
        logs: {
          projectId: null,
          events: [],
          lastBefore: null,
          hasMore: false,
          loading: false,
          selectedEventId: null,
          selectedEventJson: '',
        },
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

      function setView(view) {
        state.view = view === 'logs' ? 'logs' : 'tokens';
        qs('view_tokens').classList.toggle('hidden', state.view !== 'tokens');
        qs('view_logs').classList.toggle('hidden', state.view !== 'logs');

        for (const el of document.querySelectorAll('.navItem')) {
          el.classList.toggle('active', el.getAttribute('data-view') === state.view);
        }

        if (state.view === 'logs') {
          maybeAutoLoadLogs();
        }
      }

      function viewFromHash() {
        const h = (window.location.hash || '').replace('#', '').trim().toLowerCase();
        if (h === 'logs') return 'logs';
        return 'tokens';
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

      function renderLogsProjects() {
        const sel = qs('logs_project');
        sel.innerHTML = '';
        for (const p of state.projects) {
          const opt = document.createElement('option');
          opt.value = String(p.id);
          opt.textContent = `${p.id} - ${p.name}`;
          sel.appendChild(opt);
        }
        if (!state.logs.projectId) {
          const first = state.projects[0];
          state.logs.projectId = first ? first.id : null;
        }
        if (state.logs.projectId != null) {
          sel.value = String(state.logs.projectId);
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

      function fmtTime(s) {
        if (!s) return '';
        try {
          const d = new Date(s);
          if (Number.isNaN(d.getTime())) return String(s);
          return d.toLocaleString();
        } catch {
          return String(s);
        }
      }

      function renderLogsRows() {
        const tbody = qs('logs_rows');
        tbody.innerHTML = '';
        for (const e of state.logs.events) {
          const tr = document.createElement('tr');
          tr.style.cursor = 'pointer';
          tr.addEventListener('click', () => openEventDetail(e.id));
          tr.innerHTML = `
            <td class="mono">${escapeHtml(fmtTime(e.timestamp))}</td>
            <td>${escapeHtml(e.level || '')}</td>
            <td>${escapeHtml(e.environment || '')}</td>
            <td>${escapeHtml(e.release || '')}</td>
            <td>${escapeHtml(e.message || '')}</td>
          `;
          tbody.appendChild(tr);
        }
      }

      function updateLogsMoreButton() {
        qs('logs_more').disabled = !state.logs.hasMore || state.logs.loading;
      }

      function logsReadFilters() {
        const projectId = Number(qs('logs_project').value || '0') || null;
        const level = (qs('logs_level').value || '').trim();
        const environment = (qs('logs_env').value || '').trim();
        const release = (qs('logs_release').value || '').trim();
        const qstr = (qs('logs_q').value || '').trim();
        return { projectId, level, environment, release, q: qstr };
      }

      function logsBuildQuery(params) {
        const parts = [];
        if (params.limit != null) parts.push(`limit=${encodeURIComponent(String(params.limit))}`);
        if (params.before) parts.push(`before=${encodeURIComponent(String(params.before))}`);
        if (params.level) parts.push(`level=${encodeURIComponent(params.level)}`);
        if (params.environment) parts.push(`environment=${encodeURIComponent(params.environment)}`);
        if (params.release) parts.push(`release=${encodeURIComponent(params.release)}`);
        if (params.q) parts.push(`q=${encodeURIComponent(params.q)}`);
        return parts.length ? `?${parts.join('&')}` : '';
      }

      async function logsFetchPage({ replace }) {
        showErr(qs('logs_err'), '');
        const { projectId, level, environment, release, q: qstr } = logsReadFilters();
        state.logs.projectId = projectId;
        if (!projectId) {
          state.logs.events = [];
          state.logs.lastBefore = null;
          state.logs.hasMore = false;
          renderLogsRows();
          updateLogsMoreButton();
          return;
        }

        const limit = 50;
        const before = replace ? null : state.logs.lastBefore;
        const url = `/api/admin/projects/${projectId}/events` + logsBuildQuery({ limit, before, level, environment, release, q: qstr });

        state.logs.loading = true;
        updateLogsMoreButton();
        qs('logs_load').disabled = true;
        try {
          const rows = await api(url);
          if (replace) state.logs.events = [];
          state.logs.events = state.logs.events.concat(rows || []);
          const last = state.logs.events[state.logs.events.length - 1];
          state.logs.lastBefore = last ? last.timestamp : null;
          state.logs.hasMore = Array.isArray(rows) && rows.length === limit;
          renderLogsRows();
        } catch (e) {
          showErr(qs('logs_err'), e.message);
        } finally {
          state.logs.loading = false;
          qs('logs_load').disabled = false;
          updateLogsMoreButton();
        }
      }

      async function logsRefresh() {
        state.logs.lastBefore = null;
        state.logs.hasMore = false;
        state.logs.events = [];
        renderLogsRows();
        updateLogsMoreButton();
        await logsFetchPage({ replace: true });
      }

      async function logsLoadMore() {
        await logsFetchPage({ replace: false });
      }

      async function maybeAutoLoadLogs() {
        if (state.logs.loading) return;
        if (!state.projects.length) return;
        if (!qs('logs_project').value) {
          renderLogsProjects();
        }
        if (!state.logs.events.length) {
          await logsRefresh();
        }
      }

      function openModal() {
        qs('logs_modal').classList.remove('hidden');
      }

      function closeModal() {
        qs('logs_modal').classList.add('hidden');
        qs('logs_modal_msg').textContent = '';
      }

      async function openEventDetail(eventId) {
        showErr(qs('logs_err'), '');
        const projectId = state.logs.projectId;
        if (!projectId) return;
        qs('logs_modal_msg').textContent = '';
        qs('logs_payload').textContent = 'Loading...';
        qs('logs_modal_meta').textContent = `${projectId} / ${eventId}`;
        state.logs.selectedEventId = eventId;
        state.logs.selectedEventJson = '';
        openModal();
        try {
          const ev = await api(`/api/admin/projects/${projectId}/events/${eventId}`);
          const meta = [
            `project=${ev.project_id}`,
            `id=${ev.id}`,
            `time=${ev.timestamp}`,
            `level=${ev.level}`,
            ev.environment ? `env=${ev.environment}` : null,
            ev.release ? `release=${ev.release}` : null,
            ev.server_name ? `server=${ev.server_name}` : null,
          ].filter(Boolean).join('  ');
          qs('logs_modal_meta').textContent = meta;
          const jsonStr = JSON.stringify(ev.payload || {}, null, 2);
          state.logs.selectedEventJson = jsonStr;
          qs('logs_payload').textContent = jsonStr;
        } catch (e) {
          qs('logs_payload').textContent = '';
          showErr(qs('logs_err'), e.message);
          closeModal();
        }
      }

      async function copySelectedJson() {
        const jsonStr = state.logs.selectedEventJson || '';
        if (!jsonStr) return;
        try {
          await navigator.clipboard.writeText(jsonStr);
          qs('logs_modal_msg').textContent = 'Copied JSON to clipboard.';
          qs('logs_modal_msg').className = 'ok';
        } catch (e) {
          qs('logs_modal_msg').textContent = 'Copy failed. Your browser may block clipboard access.';
          qs('logs_modal_msg').className = 'error';
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
        showErr(qs('logs_err'), '');

        state.projects = await api('/api/admin/projects');
        state.tokens = await api('/api/admin/tokens');

        renderProjects();
        renderLogsProjects();
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
      qs('refresh').addEventListener('click', async () => {
        await loadAll();
        if (state.view === 'logs') {
          await logsRefresh();
        }
      });
      qs('logout').addEventListener('click', doLogout);

      qs('logs_load').addEventListener('click', logsRefresh);
      qs('logs_more').addEventListener('click', logsLoadMore);
      qs('logs_project').addEventListener('change', logsRefresh);
      qs('logs_level').addEventListener('change', logsRefresh);
      qs('logs_env').addEventListener('keydown', (e) => { if (e.key === 'Enter') logsRefresh(); });
      qs('logs_release').addEventListener('keydown', (e) => { if (e.key === 'Enter') logsRefresh(); });
      qs('logs_q').addEventListener('keydown', (e) => { if (e.key === 'Enter') logsRefresh(); });

      qs('logs_modal_close').addEventListener('click', closeModal);
      qs('logs_copy').addEventListener('click', copySelectedJson);
      qs('logs_modal').addEventListener('click', (e) => {
        if (e.target && e.target.id === 'logs_modal') closeModal();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
      });

      for (const el of document.querySelectorAll('.navItem')) {
        const v = el.getAttribute('data-view');
        const go = () => { window.location.hash = '#' + v; };
        el.addEventListener('click', go);
        el.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') go();
        });
      }

      window.addEventListener('hashchange', () => {
        setView(viewFromHash());
      });

      setView(viewFromHash());

      loadAll().catch(e => {
        showErr(qs('access_err'), e.message);
      });
    </script>
  </body>
</html>"""

    html = html.replace("__EMAIL__", email)
    return HTMLResponse(html, status_code=200)
