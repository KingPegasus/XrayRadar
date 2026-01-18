from datetime import datetime, timezone
import os
import secrets

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import (
    _forbidden,
    _get_session_email,
    _get_user_session_email,
    _parse_admin_allowlist,
    _unauthorized,
)
from .db import get_db
from .models import Token, TokenProjectAccess, User


def _is_session_admin(request: Request) -> bool:
    email = _get_session_email(request)
    if not email:
        return False
    allowlist = _parse_admin_allowlist()
    return bool(allowlist) and email in allowlist


def require_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    email = _get_user_session_email(request)
    if not email:
        raise _unauthorized("Not logged in")
    q = select(User).where(User.email == email)
    row = db.execute(q).scalars().first()
    if row is None:
        raise _unauthorized("Not logged in")
    return row


def get_current_token(
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
) -> Token:
    token_value = (x_xrayradar_token or "").strip()
    if not token_value:
        raise _unauthorized("Missing token")

    q = select(Token).where(Token.token == token_value)
    row = db.execute(q).scalars().first()
    if row is None:
        raise _unauthorized("Invalid token")
    if row.revoked_at is not None:
        raise _unauthorized("Token revoked")
    return row


def require_project_access(
    project_id: int,
    db: Session = Depends(get_db),
    token: Token = Depends(get_current_token),
) -> Token:
    if token.is_admin:
        return token

    q = (
        select(TokenProjectAccess)
        .where(TokenProjectAccess.token_id == token.id)
        .where(TokenProjectAccess.project_id == project_id)
        .where(TokenProjectAccess.revoked_at.is_(None))
    )
    access = db.execute(q).scalars().first()
    if access is None:
        raise _forbidden("Token has no access to this project")
    return token


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
) -> Token:
    if _is_session_admin(request):
        email = _get_session_email(request) or "admin"
        return Token(name=email, token="", is_admin=True)

    token = get_current_token(db=db, x_xrayradar_token=x_xrayradar_token)
    if token.is_admin:
        return token
    raise _forbidden("Admin privileges required")


def admin_me(request: Request) -> dict:
    if not _is_session_admin(request):
        raise _unauthorized("Not logged in")
    return {"email": _get_session_email(request)}


def authorize_ingest_for_project(
    *,
    project_id: int,
    db: Session,
    x_xrayradar_token: str | None,
) -> None:
    token = get_current_token(db=db, x_xrayradar_token=x_xrayradar_token)
    require_project_access(project_id=project_id, db=db, token=token)


def health() -> dict:
    return {
        "status": "ok",
        "auth_required": True,
    }


def _new_admin_token_value() -> str:
    return secrets.token_urlsafe(32)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_github_oauth_configured() -> bool:
    return bool((os.getenv("XRAYRADAR_GITHUB_CLIENT_ID") or "").strip()) and bool(
        (os.getenv("XRAYRADAR_GITHUB_REDIRECT_URI") or "").strip()
    )
