"""User API package: projects, dashboard, tokens, issues, alerts, account."""

from fastapi import APIRouter

from . import account
from . import alerts
from . import dashboard
from . import issues
from . import projects
from . import team
from . import tokens

router = APIRouter()
router.include_router(projects.router)
router.include_router(dashboard.router)
router.include_router(tokens.router)
router.include_router(issues.router)
router.include_router(alerts.router)
router.include_router(team.router)
router.include_router(account.router)

__all__ = ["router"]
