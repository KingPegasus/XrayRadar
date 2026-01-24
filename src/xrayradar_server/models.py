from datetime import datetime, timezone
import os
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import CHAR, TypeDecorator

from .db import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_sqlite() -> bool:
    return os.getenv("XRAYRADAR_DATABASE_URL", "").startswith("sqlite:")


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    owner: Mapped["User | None"] = relationship("User", back_populates="projects")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4)
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

    fingerprint: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    payload: Mapped[dict] = mapped_column(
        JSON if _is_sqlite() else JSONB, nullable=False)

    project: Mapped[Project] = relationship(Project)


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(
        String(320), nullable=True, index=True)
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

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

    user: Mapped["User | None"] = relationship("User", back_populates="tokens")


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


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(
        String(32), nullable=False, default="Free")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, default=_utcnow_naive
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

    projects: Mapped[list[Project]] = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    tokens: Mapped[list[Token]] = relationship(
        "Token", back_populates="user"
    )
    token_requests: Mapped[list["TokenRequest"]] = relationship(
        "TokenRequest", back_populates="user", cascade="all, delete-orphan"
    )


class TokenRequest(Base):
    __tablename__ = "token_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, default=_utcnow_naive
    )
    fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    fulfilled_token_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tokens.id"), nullable=True, index=True
    )

    user: Mapped[User] = relationship("User", back_populates="token_requests")
    fulfilled_token: Mapped[Token | None] = relationship("Token")
