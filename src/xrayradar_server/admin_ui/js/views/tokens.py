"""Token management view for admin UI."""

TOKENS_JS = """function renderProjects() {
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
}"""
