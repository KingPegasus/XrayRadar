"""Token requests view for admin UI."""

REQUESTS_JS = """function renderTokenRequests() {
  const tbody = qs('req_rows');
  tbody.innerHTML = '';
  for (const r of state.tokenRequests) {
    const tr = document.createElement('tr');
    const fulfilled = r.fulfilled_at ? escapeHtml(r.fulfilled_at) : '';
    const btn = document.createElement('button');
    btn.className = 'small primary';
    btn.textContent = r.fulfilled_at ? 'Fulfilled' : 'Fulfill';
    btn.disabled = !!r.fulfilled_at;
    btn.addEventListener('click', async () => {
      await fulfillTokenRequest(r.id);
    });
    tr.innerHTML = `
      <td>${r.id}</td>
      <td>${escapeHtml(r.user_email || '')}</td>
      <td>${escapeHtml(r.name || '')}</td>
      <td>${escapeHtml(r.created_at || '')}</td>
      <td>${fulfilled}</td>
      <td></td>
    `;
    tr.children[5].appendChild(btn);
    tbody.appendChild(tr);
  }
}

async function refreshTokenRequests() {
  showErr(qs('req_err'), '');
  qs('req_out').textContent = '';
  try {
    state.tokenRequests = await api('/api/admin/token-requests');
    renderTokenRequests();
  } catch (e) {
    showErr(qs('req_err'), e.message);
  }
}

async function fulfillTokenRequest(id) {
  showErr(qs('req_err'), '');
  qs('req_out').textContent = '';
  try {
    const out = await api(`/api/admin/token-requests/${id}/fulfill`, { method: 'POST' });
    qs('req_out').textContent = `Fulfilled request ${id}. Token id=${out.id}. Token value (copy now): ${out.token}`;
    await refreshTokenRequests();
    await loadAll();
  } catch (e) {
    showErr(qs('req_err'), e.message);
  }
}"""
