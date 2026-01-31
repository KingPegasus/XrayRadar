from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import (
    forbidden,
    get_session_email,
    get_user_session_email,
    parse_admin_allowlist,
    unauthorized,
)
from .db import get_db
from .models import Token, TokenProjectAccess, User

EMAIL_VERIFICATION_REQUIRED_DETAIL = "Email verification required for this action."


def _is_session_admin(request: Request) -> bool:
    email = get_session_email(request)
    if not email:
        return False
    allowlist = parse_admin_allowlist()
    return bool(allowlist) and email in allowlist


def require_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    email = get_user_session_email(request)
    if not email:
        raise unauthorized("Not logged in")
    q = select(User).where(User.email == email)
    row = db.execute(q).scalars().first()
    if row is None:
        raise unauthorized("Not logged in")
    return row


def require_verified_user(user: User = Depends(require_user)) -> User:
    """Require the user to have a verified email for sensitive actions."""
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail=EMAIL_VERIFICATION_REQUIRED_DETAIL,
        )
    return user


def get_current_token(
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
) -> Token:
    token_value = (x_xrayradar_token or "").strip()
    if not token_value:
        raise unauthorized("Missing token")

    q = select(Token).where(Token.token == token_value)
    row = db.execute(q).scalars().first()
    if row is None:
        raise unauthorized("Invalid token")
    if row.revoked_at is not None:
        raise unauthorized("Token revoked")
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
        raise forbidden("Token has no access to this project")
    return token


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
    x_xrayradar_token: str | None = Header(
        default=None, alias="X-Xrayradar-Token"),
) -> Token:
    if _is_session_admin(request):
        email = get_session_email(request) or "admin"
        # bandit: token is intentionally empty for session-admin (not a secret)
        return Token(name=email, token="", is_admin=True)  # nosec B106

    token = get_current_token(db=db, x_xrayradar_token=x_xrayradar_token)
    if token.is_admin:
        return token
    raise forbidden("Admin privileges required")


def admin_me(request: Request) -> dict:
    if not _is_session_admin(request):
        raise unauthorized("Not logged in")
    return {"email": get_session_email(request)}


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
