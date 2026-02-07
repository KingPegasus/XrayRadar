"""Users management view for admin UI."""

USERS_JS = """function renderUsers() {
  const tbody = qs('users_rows');
  tbody.innerHTML = '';
  for (const u of state.users) {
    const tr = document.createElement('tr');
    const planBadgeClass = u.plan === 'Basic' ? 'admin' : (u.plan === 'Pro' ? 'admin' : '');
    tr.innerHTML = `
      <td>${u.id}</td>
      <td>${escapeHtml(u.email || '')}</td>
      <td><span class="pill ${planBadgeClass}">${escapeHtml(u.plan)}</span></td>
      <td>${u.event_count.toLocaleString()}</td>
      <td>${escapeHtml(u.created_at ? u.created_at.split('T')[0] : '')}</td>
      <td>
        <select class="plan-select" data-user-id="${u.id}" style="width: 80px; padding: 6px">
          <option value="Free" ${u.plan === 'Free' ? 'selected' : ''}>Free</option>
          <option value="Basic" ${u.plan === 'Basic' ? 'selected' : ''}>Basic</option>
          <option value="Pro" ${u.plan === 'Pro' ? 'selected' : ''}>Pro</option>
        </select>
      </td>
    `;
    tbody.appendChild(tr);
  }
  // Add event listeners to plan selects
  for (const sel of tbody.querySelectorAll('.plan-select')) {
    sel.addEventListener('change', async (e) => {
      const userId = parseInt(e.target.getAttribute('data-user-id'), 10);
      const newPlan = e.target.value;
      await updateUserPlan(userId, newPlan);
    });
  }
}

async function refreshUsers() {
  showErr(qs('users_err'), '');
  qs('users_out').textContent = '';
  try {
    state.users = await api('/api/admin/users');
    renderUsers();
  } catch (e) {
    showErr(qs('users_err'), e.message);
  }
}

async function updateUserPlan(userId, newPlan) {
  showErr(qs('users_err'), '');
  qs('users_out').textContent = '';
  try {
    await api(`/api/admin/users/${userId}/plan`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan: newPlan }),
    });
    qs('users_out').textContent = `Updated user ${userId} to ${newPlan} plan.`;
    await refreshUsers();
  } catch (e) {
    showErr(qs('users_err'), e.message);
    await refreshUsers(); // Reset to actual state
  }
}"""
