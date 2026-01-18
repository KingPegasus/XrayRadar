from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import cookie_secure, get_session_serializer, hash_password, unauthorized, verify_password
from ..db import get_db
from ..deps import require_user
from ..models import User
from ..schemas import UserLogin, UserOut, UserSignup

router = APIRouter()


@router.post("/auth/logout")
def logout(_: Request, response: Response) -> dict:
    response.delete_cookie("xrayradar_session", path="/")
    response.delete_cookie("xrayradar_user_session", path="/")
    return {"ok": True}


@router.post("/auth/signup", response_model=UserOut)
def signup(payload: UserSignup, response: Response, db: Session = Depends(get_db)) -> UserOut:
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

    row = User(
        email=email,
        password_hash=hash_password(payload.password),
        plan=plan,
        last_login_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

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

    return UserOut(id=row.id, email=row.email, plan=row.plan, created_at=row.created_at)


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

    return UserOut(id=row.id, email=row.email, plan=row.plan, created_at=row.created_at)


@router.get("/api/me", response_model=UserOut)
def me(user: User = Depends(require_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, plan=user.plan, created_at=user.created_at)
