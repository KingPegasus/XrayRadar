"""Deletion requests view for admin UI."""

DELETIONS_JS = """function renderDeletionRequests() {
  const tbody = qs('del_rows');
  tbody.innerHTML = '';
  if (state.deletionRequests.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="5" style="color: var(--muted); text-align: center; padding: 20px">No pending deletion requests</td>';
    tbody.appendChild(tr);
    return;
  }
  for (const r of state.deletionRequests) {
    const tr = document.createElement('tr');
    const btn = document.createElement('button');
    btn.className = 'small danger';
    btn.textContent = 'Delete Account';
    btn.addEventListener('click', async () => {
      if (!confirm(`Are you sure you want to permanently delete user ${r.user_email} and all their data? This cannot be undone.`)) {
        return;
      }
      await fulfillDeletionRequest(r.id, r.user_email);
    });
    tr.innerHTML = `
      <td>${r.id}</td>
      <td>${escapeHtml(r.user_email || '')}</td>
      <td>${escapeHtml(r.reason || '(no reason provided)')}</td>
      <td>${escapeHtml(r.created_at ? r.created_at.split('T')[0] : '')}</td>
      <td></td>
    `;
    tr.children[4].appendChild(btn);
    tbody.appendChild(tr);
  }
}

async function refreshDeletionRequests() {
  showErr(qs('del_err'), '');
  qs('del_out').textContent = '';
  try {
    state.deletionRequests = await api('/api/admin/deletion-requests');
    renderDeletionRequests();
  } catch (e) {
    showErr(qs('del_err'), e.message);
  }
}

async function fulfillDeletionRequest(requestId, userEmail) {
  showErr(qs('del_err'), '');
  qs('del_out').textContent = '';
  try {
    await api(`/api/admin/deletion-requests/${requestId}/fulfill`, { method: 'POST' });
    qs('del_out').textContent = `User ${userEmail} and all associated data deleted.`;
    await refreshDeletionRequests();
  } catch (e) {
    showErr(qs('del_err'), e.message);
  }
}"""
