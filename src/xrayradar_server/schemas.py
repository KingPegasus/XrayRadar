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
