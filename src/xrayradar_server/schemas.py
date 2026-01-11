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
