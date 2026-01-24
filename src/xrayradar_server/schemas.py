from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectOut(BaseModel):
    id: int
    name: str


class EventIn(BaseModel):
    event_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    level: str
    message: str
    contexts: Optional[dict[str, Any]] = None
    exception: Optional[dict[str, Any]] = None
    breadcrumbs: Optional[list[dict[str, Any]]] = None
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


class UserOut(BaseModel):
    id: int
    email: str
    plan: str
    created_at: datetime


class UserProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class UserProjectOut(BaseModel):
    id: int
    name: str


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


class IssueSummaryOut(BaseModel):
    fingerprint: str
    count: int
    first_seen: datetime
    last_seen: datetime
    level: str
    message: str
    environment: Optional[str] = None
    release: Optional[str] = None


class AdminTokenRequestOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    name: str
    note: Optional[str] = None
    created_at: datetime
    fulfilled_at: Optional[datetime] = None
    fulfilled_token_id: Optional[int] = None
