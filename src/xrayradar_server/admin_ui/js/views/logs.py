"""Logs/events viewer for admin UI."""

LOGS_JS = """function renderLogsProjects() {
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
}"""
