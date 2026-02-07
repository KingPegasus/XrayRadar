"""Main JavaScript initialization for admin UI."""

from . import api, state, utils
from .views import VIEWS_JS

MAIN_JS = """function setView(view) {
  const validViews = ['dashboard', 'tokens', 'requests', 'users', 'deletions', 'logs'];
  state.view = validViews.includes(view) ? view : 'dashboard';
  qs('view_dashboard').classList.toggle('hidden', state.view !== 'dashboard');
  qs('view_tokens').classList.toggle('hidden', state.view !== 'tokens');
  qs('view_requests').classList.toggle('hidden', state.view !== 'requests');
  qs('view_users').classList.toggle('hidden', state.view !== 'users');
  qs('view_deletions').classList.toggle('hidden', state.view !== 'deletions');
  qs('view_logs').classList.toggle('hidden', state.view !== 'logs');

  for (const el of document.querySelectorAll('.navItem')) {
    el.classList.toggle('active', el.getAttribute('data-view') === state.view);
  }

  if (state.view === 'dashboard') {
    refreshDashboard();
  }
  if (state.view === 'logs') {
    maybeAutoLoadLogs();
  }
  if (state.view === 'requests') {
    refreshTokenRequests();
  }
  if (state.view === 'users') {
    refreshUsers();
  }
  if (state.view === 'deletions') {
    refreshDeletionRequests();
  }
}

function viewFromHash() {
  const h = (window.location.hash || '').replace('#', '').trim().toLowerCase();
  if (h === 'dashboard') return 'dashboard';
  if (h === 'tokens') return 'tokens';
  if (h === 'logs') return 'logs';
  if (h === 'deletions') return 'deletions';
  if (h === 'requests') return 'requests';
  if (h === 'users') return 'users';
  return 'dashboard';
}

async function loadAll() {
  showErr(qs('create_err'), '');
  showErr(qs('access_err'), '');
  showErr(qs('logs_err'), '');
  showErr(qs('req_err'), '');
  showErr(qs('users_err'), '');
  showErr(qs('del_err'), '');
  showErr(qs('dashboard_err'), '');

  state.projects = await api('/api/admin/projects');
  state.tokens = await api('/api/admin/tokens');

  renderProjects();
  renderLogsProjects();
  renderTokens();
  if (state.view === 'dashboard') {
    await refreshDashboard();
  }
  if (state.view === 'requests') {
    await refreshTokenRequests();
  }
  if (state.view === 'users') {
    await refreshUsers();
  }
  if (state.view === 'deletions') {
    await refreshDeletionRequests();
  }

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
  if (state.view === 'dashboard') {
    await refreshDashboard();
  }
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
});"""

# Combine all JavaScript modules
ALL_JS = (
    state.STATE_JS
    + "\n\n"
    + utils.UTILS_JS
    + "\n\n"
    + api.API_JS
    + "\n\n"
    + VIEWS_JS
    + "\n\n"
    + MAIN_JS
)
