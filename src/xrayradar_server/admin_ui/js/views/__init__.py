"""Views module for admin UI."""

from . import deletions, logs, requests, tokens, users

VIEWS_JS = (
    tokens.TOKENS_JS
    + "\n\n"
    + requests.REQUESTS_JS
    + "\n\n"
    + users.USERS_JS
    + "\n\n"
    + deletions.DELETIONS_JS
    + "\n\n"
    + logs.LOGS_JS
)
