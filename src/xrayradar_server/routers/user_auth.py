import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import cookie_secure, get_session_serializer, hash_password, unauthorized, verify_password
from ..constants import RESEND_API_KEY, RESEND_FROM_EMAIL, XRAYRADAR_BASE_URL
from ..db import get_db
from ..deps import require_user
from ..models import User
from ..schemas import UserLogin, UserOut, UserSignup

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_verification_token() -> str:
    """Generate a secure random verification token."""
    return secrets.token_urlsafe(32)


def _send_verification_email(email: str, token: str) -> None:
    """Send verification email via Resend. No-op if Resend not configured."""
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        logger.warning("Resend not configured, skipping verification email for %s", email)
        return
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        verify_link = f"{XRAYRADAR_BASE_URL.rstrip('/')}/verify-email?token={token}"
        subject = "[XrayRadar] Verify your email address"
        html = f"""
        <p>Welcome to XrayRadar!</p>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verify_link}" style="display: inline-block; padding: 12px 24px; background: #4f7cff; color: white; text-decoration: none; border-radius: 6px;">Verify Email</a></p>
        <p>Or copy and paste this URL into your browser:</p>
        <p><a href="{verify_link}">{verify_link}</a></p>
        <p>This link will expire in 24 hours.</p>
        <p>If you didn't create an account, you can ignore this email.</p>
        """
        resend.Emails.send(
            {
                "from": RESEND_FROM_EMAIL,
                "to": [email],
                "subject": subject,
                "html": html,
            }
        )
        logger.info("Verification email sent to %s", email)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to send verification email to %s: %s", email, e)


@router.post("/auth/logout")
def logout(_: Request, response: Response) -> dict:
    response.delete_cookie("xrayradar_session", path="/")
    response.delete_cookie("xrayradar_user_session", path="/")
    return {"ok": True}


@router.post("/auth/signup", response_model=UserOut)
def signup(
    payload: UserSignup,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> UserOut:
    email = (payload.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    plan = (payload.plan or "").strip() or "Free"
    if plan not in {"Free", "Basic"}:
        raise HTTPException(status_code=400, detail="Invalid plan")

    exists = db.execute(select(User).where(
        User.email == email)).scalars().first()
    if exists is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    verification_token = _generate_verification_token()

    row = User(
        email=email,
        password_hash=hash_password(payload.password),
        plan=plan,
        email_verified=False,
        verification_token=verification_token,
        last_login_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # Send verification email in background
    background_tasks.add_task(_send_verification_email, email, verification_token)

    s = get_session_serializer()
    session_cookie = s.dumps(
        {"email": row.email, "ts": int(datetime.now(timezone.utc).timestamp())}
    )
    response.set_cookie(
        "xrayradar_user_session",
        session_cookie,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        path="/",
        max_age=60 * 60 * 24 * 30,
    )

    return UserOut(
        id=row.id,
        email=row.email,
        plan=row.plan,
        email_verified=row.email_verified,
        created_at=row.created_at,
    )


@router.post("/auth/login", response_model=UserOut)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> UserOut:
    email = (payload.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Invalid email")

    row = db.execute(select(User).where(User.email == email)).scalars().first()
    if row is None:
        raise unauthorized("Invalid credentials")
    if not verify_password(payload.password, row.password_hash):
        raise unauthorized("Invalid credentials")

    row.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    s = get_session_serializer()
    session_cookie = s.dumps(
        {"email": row.email, "ts": int(datetime.now(timezone.utc).timestamp())}
    )
    response.set_cookie(
        "xrayradar_user_session",
        session_cookie,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        path="/",
        max_age=60 * 60 * 24 * 30,
    )

    return UserOut(
        id=row.id,
        email=row.email,
        plan=row.plan,
        email_verified=row.email_verified,
        created_at=row.created_at,
    )


@router.get("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)) -> dict:
    """Verify email using the token from the verification email."""
    if not token or len(token) < 10:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    user = db.execute(
        select(User).where(User.verification_token == token)
    ).scalars().first()

    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    if user.email_verified:
        return {"ok": True, "message": "Email already verified"}

    user.email_verified = True
    user.verification_token = None  # Clear token after use
    db.commit()

    return {"ok": True, "message": "Email verified successfully"}


@router.post("/auth/resend-verification")
def resend_verification(
    background_tasks: BackgroundTasks,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    """Resend verification email to the logged-in user."""
    if user.email_verified:
        return {"ok": True, "message": "Email already verified"}

    # Generate new token
    new_token = _generate_verification_token()
    user.verification_token = new_token
    db.commit()

    # Send verification email in background
    background_tasks.add_task(_send_verification_email, user.email, new_token)

    return {"ok": True, "message": "Verification email sent"}


@router.get("/api/me", response_model=UserOut)
def me(user: User = Depends(require_user)) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        plan=user.plan,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )
