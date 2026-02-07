import os

GITHUB_OAUTH_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # nosec B105 (URL, not a password)

# Event storage limits per plan tier
TIER_EVENT_LIMITS = {
    "Free": 1_000,
    "Basic": 15_000,
    "Teams": 25_000,
    "Teams Pro": 50_000,
}

# Warning threshold (percentage) - warn users when they reach this % of their limit
TIER_WARNING_THRESHOLD = 0.8  # 80%

# Resend email (optional; if RESEND_API_KEY unset, email alerts are disabled)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "")
# Base URL for links in alert emails (e.g. https://app.example.com)
XRAYRADAR_BASE_URL = os.environ.get("XRAYRADAR_BASE_URL", "http://localhost:8001")

# Max additional alert recipients per project (besides owner)
MAX_ALERT_RECIPIENTS = 20

# Minimum cooldown (minutes) for email alerts by plan tier. Free: None = no email alerts.
MIN_COOLDOWN_MINUTES_BY_PLAN = {
    "Free": None,
    "Basic": 10,
    "Teams": 1,
    "Teams Pro": 1,
}

# Max team members (invited users) per plan. Free/Basic have no team access (0).
MAX_TEAM_MEMBERS_BY_PLAN = {
    "Teams": 5,
    "Teams Pro": 10,
}

# Rate limiting (requests per window; format: "N/minute", "N/hour", "N/day")
RATE_LIMIT_AUTH = os.environ.get("XRAYRADAR_RATE_LIMIT_AUTH", "5/minute")
RATE_LIMIT_EVENT_INGEST = os.environ.get("XRAYRADAR_RATE_LIMIT_EVENT_INGEST", "100/minute")
