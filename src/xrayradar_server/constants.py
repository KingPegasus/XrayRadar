GITHUB_OAUTH_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # nosec B105 (URL, not a password)

# Event storage limits per plan tier
TIER_EVENT_LIMITS = {
    "Free": 5_000,
    "Basic": 50_000,
    "Pro": None,  # None means unlimited
}

# Warning threshold (percentage) - warn users when they reach this % of their limit
TIER_WARNING_THRESHOLD = 0.8  # 80%

