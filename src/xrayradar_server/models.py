from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import CHAR, TypeDecorator

from .db import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JSONOrJSONB(TypeDecorator):
    """JSON for SQLite, JSONB for PostgreSQL. Resolved at compile time so tests work with either dialect."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":  # pragma: no cover - tests use SQLite
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


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
    alert_settings: Mapped["ProjectAlertSettings | None"] = relationship(
        "ProjectAlertSettings", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    alert_recipients: Mapped[list["ProjectAlertRecipient"]] = relationship(
        "ProjectAlertRecipient", back_populates="project", cascade="all, delete-orphan"
    )


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
        JSONOrJSONB(), nullable=False)

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

    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    verification_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    password_reset_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

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
    deletion_requests: Mapped[list["DeletionRequest"]] = relationship(
        "DeletionRequest", back_populates="user", cascade="all, delete-orphan"
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


class ProjectAlertSettings(Base):
    __tablename__ = "project_alert_settings"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), primary_key=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    level_filter: Mapped[str] = mapped_column(
        String(32), nullable=False, default="error"
    )
    cooldown_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped[Project] = relationship(
        "Project", back_populates="alert_settings"
    )


class ProjectAlertRecipient(Base):
    __tablename__ = "project_alert_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)

    project: Mapped[Project] = relationship(
        "Project", back_populates="alert_recipients"
    )

    __table_args__ = (UniqueConstraint("project_id", "email", name="uq_project_alert_recipients_project_email"),)


class AlertCooldown(Base):
    __tablename__ = "alert_cooldown"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False, primary_key=True
    )
    fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False, primary_key=True
    )
    last_notified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, default=_utcnow_naive
    )
    fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

    user: Mapped[User] = relationship("User", back_populates="deletion_requests")
