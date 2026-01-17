import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(2048), nullable=False)

    environment: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True)
    release: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True)
    server_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    project: Mapped[Project] = relationship(Project)


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(
        String(320), nullable=True, index=True)
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True)

    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, default=_utcnow_naive
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True)

    project_access: Mapped[list["TokenProjectAccess"]] = relationship(
        "TokenProjectAccess", back_populates="token_ref", cascade="all, delete-orphan"
    )


class TokenProjectAccess(Base):
    __tablename__ = "token_project_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tokens.id"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, default=_utcnow_naive
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True)

    token_ref: Mapped[Token] = relationship(
        "Token", back_populates="project_access")
    project: Mapped[Project] = relationship(Project)
