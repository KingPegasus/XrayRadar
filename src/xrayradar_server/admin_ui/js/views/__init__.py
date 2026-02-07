"""Views module for admin UI."""

from . import dashboard, deletions, logs, requests, tokens, users

VIEWS_JS = (
    dashboard.DASHBOARD_JS
    + "\n\n"
    + tokens.TOKENS_JS
    + "\n\n"
    + requests.REQUESTS_JS
    + "\n\n"
    + users.USERS_JS
    + "\n\n"
    + deletions.DELETIONS_JS
    + "\n\n"
    + logs.LOGS_JS
)
