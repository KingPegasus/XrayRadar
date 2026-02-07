"""Dashboard view JavaScript for admin UI."""

DASHBOARD_JS = """async function refreshDashboard() {
  showErr(qs('dashboard_err'), '');
  try {
    const stats = await api('/api/admin/stats');
    renderDashboardStats(stats);
    const updatedEl = document.getElementById('dashboard_updated');
    if (updatedEl) updatedEl.textContent = 'Last updated at ' + new Date().toLocaleTimeString();
  } catch (e) {
    showErr(qs('dashboard_err'), e.message);
  }
}

function renderDashboardStats(stats) {
  const container = qs('dashboard_stats');
  container.innerHTML = '';

  const groups = [
    { title: 'Projects', view: 'logs', items: [
      { label: 'Total Projects', value: stats.projects_total, highlight: 'blue' }
    ]},
    { title: 'Tokens', view: 'tokens', items: [
      { label: 'Total Tokens', value: stats.tokens_total, highlight: 'blue' },
      { label: 'Active', value: stats.tokens_active, highlight: 'green' },
      { label: 'Revoked', value: stats.tokens_revoked, highlight: 'red' }
    ]},
    { title: 'Users', view: 'users', items: [
      { label: 'Free', value: stats.users_free, highlight: null },
      { label: 'Basic', value: stats.users_basic, highlight: 'yellow' },
      { label: 'Teams', value: stats.users_teams, highlight: 'purple' },
      { label: 'Teams Pro', value: stats.users_teams_pro, highlight: 'purple' }
    ]},
    { title: 'Events', view: 'logs', items: [
      { label: 'Total Events', value: stats.events_total, highlight: 'blue' }
    ]},
    { title: 'Emails', items: [
      { label: 'Total Sent', value: stats.emails_total, highlight: 'green' },
      { label: 'Verification', value: stats.emails_verification, highlight: null },
      { label: 'Password Reset', value: stats.emails_password_reset, highlight: null },
      { label: 'Error Alerts', value: stats.emails_error_alert, highlight: 'yellow' },
      { label: 'Team Invites', value: stats.emails_team_invite, highlight: null },
      { label: 'Failed', value: stats.emails_failed, highlight: 'red' }
    ]}
  ];

  groups.forEach(group => {
    const groupCard = document.createElement('div');
    groupCard.className = 'dashboard-card';
    if (group.view) {
      groupCard.classList.add('clickable');
      groupCard.setAttribute('role', 'button');
      groupCard.setAttribute('tabindex', '0');
      groupCard.setAttribute('aria-label', 'Go to ' + group.title);
      groupCard.addEventListener('click', () => { window.location.hash = '#' + group.view; });
      groupCard.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); window.location.hash = '#' + group.view; }
      });
    }

    const title = document.createElement('div');
    title.className = 'dashboard-card-title';
    title.textContent = group.title;
    groupCard.appendChild(title);

    group.items.forEach(item => {
      const itemDiv = document.createElement('div');
      itemDiv.className = 'dashboard-stat-item';
      const label = document.createElement('div');
      label.className = 'dashboard-stat-label';
      label.textContent = item.label;
      const value = document.createElement('div');
      value.className = 'dashboard-stat-value';
      if (item.highlight) value.classList.add('highlight-' + item.highlight);
      value.textContent = typeof item.value === 'number' ? item.value.toLocaleString() : item.value;
      itemDiv.appendChild(label);
      itemDiv.appendChild(value);
      groupCard.appendChild(itemDiv);
    });

    container.appendChild(groupCard);
  });
}
"""
