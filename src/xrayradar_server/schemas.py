from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectOut(BaseModel):
    id: int
    name: str


class BreadcrumbIn(BaseModel):
    """A single breadcrumb entry capturing an event leading up to an error."""

    timestamp: Optional[datetime] = None
    type: str = "default"  # default, http, navigation, ui, console, error, query, user
    category: Optional[str] = None
    message: Optional[str] = None
    level: str = "info"  # debug, info, warning, error
    data: Optional[dict[str, Any]] = None


class EventIn(BaseModel):
    event_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    level: str
    message: str
    contexts: Optional[dict[str, Any]] = None
    exception: Optional[dict[str, Any]] = None
    breadcrumbs: Optional[list[BreadcrumbIn]] = None
    fingerprint: Optional[list[str]] = None
    modules: Optional[dict[str, Any]] = None
    sdk: Optional[dict[str, Any]] = None
    platform: Optional[str] = None


class EventOut(BaseModel):
    id: UUID
    project_id: int
    timestamp: datetime
    level: str
    message: str
    payload: dict[str, Any]


class AdminEventListItemOut(BaseModel):
    id: UUID
    project_id: int
    timestamp: datetime
    level: str
    message: str
    environment: Optional[str] = None
    release: Optional[str] = None
    server_name: Optional[str] = None


class AdminEventOut(AdminEventListItemOut):
    payload: dict[str, Any]


class AdminUserOut(BaseModel):
    id: int
    email: str
    plan: str
    created_at: datetime
    event_count: int = 0


class AdminUserPlanUpdate(BaseModel):
    plan: str = Field(min_length=1, max_length=32)


class TokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=320)
    is_admin: bool = False


class TokenOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    is_admin: bool
    created_at: datetime
    revoked_at: Optional[datetime] = None


class TokenCreateOut(TokenOut):
    token: str


class TokenProjectGrant(BaseModel):
    token_id: int
    project_id: int


class TokenProjectAccessOut(BaseModel):
    id: int
    token_id: int
    project_id: int
    created_at: datetime
    revoked_at: Optional[datetime] = None


class UserSignup(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=200)
    plan: str = Field(default="Free", min_length=1, max_length=32)


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=64)
    new_password: str = Field(min_length=8, max_length=200)


class UserOut(BaseModel):
    id: int
    email: str
    plan: str
    email_verified: bool = False
    created_at: datetime


class UserProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class UserProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class UserProjectOut(BaseModel):
    id: int
    name: str
    is_owner: bool = True


class TeamMemberOut(BaseModel):
    user_id: int
    email: str
    project_ids: list[int]


class ProjectMemberAdd(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = Field(default=None, max_length=320)


class InviteCreate(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    project_ids: list[int] = Field(min_length=1)


class InviteOut(BaseModel):
    id: int
    email: str
    project_ids: list[int]
    expires_at: datetime
    created_at: datetime


class InviteAccept(BaseModel):
    token: str = Field(min_length=1, max_length=64)


class TokenRequestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    note: Optional[str] = Field(default=None, max_length=2000)


class TokenRequestOut(BaseModel):
    id: int
    name: str
    note: Optional[str] = None
    created_at: datetime
    fulfilled_at: Optional[datetime] = None
    fulfilled_token_id: Optional[int] = None


class UserTokenOut(BaseModel):
    id: int
    name: str
    token: str
    created_at: datetime
    revoked_at: Optional[datetime] = None


class IssueStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)  # "open", "in_progress", "resolved", "ignored"
    resolved_release: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = None


class BulkIssueStatusUpdate(BaseModel):
    fingerprints: list[str]
    status: str = Field(min_length=1, max_length=32)
    resolved_release: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = None


class IssueStatusOut(BaseModel):
    project_id: int
    fingerprint: str
    status: str
    resolved_release: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by_user_id: Optional[int] = None
    notes: Optional[str] = None
    reopened: bool = False
    created_at: datetime
    updated_at: datetime


class IssueSummaryOut(BaseModel):
    fingerprint: str
    count: int
    first_seen: datetime
    last_seen: datetime
    level: str
    message: str
    environment: Optional[str] = None
    release: Optional[str] = None
    status: Optional[str] = None
    resolved_release: Optional[str] = None
    resolved_at: Optional[datetime] = None
    reopened: Optional[bool] = None


class AdminTokenRequestOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    name: str
    note: Optional[str] = None
    created_at: datetime
    fulfilled_at: Optional[datetime] = None
    fulfilled_token_id: Optional[int] = None


class UsageOut(BaseModel):
    current_count: int
    limit: Optional[int] = None
    plan: str
    is_exceeded: bool
    is_near_limit: bool
    percentage_used: Optional[float] = None


class AlertSettingsOut(BaseModel):
    enabled: bool
    level_filter: str
    cooldown_minutes: Optional[int] = None
    min_cooldown_minutes: Optional[int] = None  # plan-based minimum (Free=no alerts, Basic=10min, Teams/Teams Pro=1min)
    additional_emails: list[str] = []
    environment_settings: list[dict[str, Any]] = []


class AlertSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    level_filter: Optional[str] = None
    cooldown_minutes: Optional[int] = None
    additional_emails: Optional[list[str]] = None
    environment_settings: Optional[list[dict[str, Any]]] = None


class DeletionRequestCreate(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=2000)


class DeletionRequestOut(BaseModel):
    id: int
    user_id: int
    reason: Optional[str] = None
    created_at: datetime
    fulfilled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class AdminDeletionRequestOut(DeletionRequestOut):
    user_email: str


class AdminStatsOut(BaseModel):
    projects_total: int = 0
    tokens_total: int = 0
    tokens_active: int = 0
    tokens_revoked: int = 0
    users_free: int = 0
    users_basic: int = 0
    users_teams: int = 0
    users_teams_pro: int = 0
    events_total: int = 0
    emails_total: int = 0
    emails_verification: int = 0
    emails_password_reset: int = 0
    emails_error_alert: int = 0
    emails_team_invite: int = 0
    emails_failed: int = 0


class DashboardTotalsOut(BaseModel):
    last_24h: int = 0
    last_7d: int = 0
    last_30d: int = 0


class DashboardUniqueIssuesOut(BaseModel):
    last_24h: int = 0
    last_7d: int = 0
    last_30d: int = 0


class DashboardTrendOut(BaseModel):
    current: int = 0
    previous: int = 0
    percent_change: float = 0.0
    direction: str = "same"  # "up" | "down" | "same"


class TopErrorOut(BaseModel):
    fingerprint: str
    message: str
    count: int
    project_id: int
    project_name: str


class DashboardStatsOut(BaseModel):
    totals: DashboardTotalsOut
    unique_issues: DashboardUniqueIssuesOut
    trend_7d: DashboardTrendOut
    trend_30d: DashboardTrendOut
    top_5_errors: list[TopErrorOut]
    trend_daily: dict[str, int] = {}  # YYYY-MM-DD -> count for chart
